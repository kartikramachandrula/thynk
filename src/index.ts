import { AppServer, AppSession, AuthenticatedRequest, PhotoData } from '@mentra/sdk';
import * as ejs from 'ejs';
import * as path from 'path';
import express from 'express';

/**
 * Interface representing a stored photo with metadata
 */
interface StoredPhoto {
  requestId: string;
  buffer: Buffer;
  timestamp: Date;
  userId: string;
  mimeType: string;
  filename: string;
  size: number;
}

const PACKAGE_NAME = process.env.PACKAGE_NAME ?? (() => { throw new Error('PACKAGE_NAME is not set in .env file'); })();
const MENTRAOS_API_KEY = process.env.MENTRAOS_API_KEY ?? (() => { throw new Error('MENTRAOS_API_KEY is not set in .env file'); })();
const PORT = parseInt(process.env.PORT || '3000');

/**
 * Photo Taker App with webview functionality for displaying photos
 * Extends AppServer to provide photo taking and webview display capabilities
 */
class ExampleMentraOSApp extends AppServer {
  private photos: Map<string, StoredPhoto> = new Map(); // Store photos by userId
  private latestPhotoTimestamp: Map<string, number> = new Map(); // Track latest photo timestamp per user
  private isStreamingPhotos: Map<string, boolean> = new Map(); // Track if we are streaming photos for a user
  private nextPhotoTime: Map<string, number> = new Map(); // Track next photo time for a user
  private displayText: string = ''; // Store text to display

  constructor() {
    super({
      packageName: PACKAGE_NAME,
      apiKey: MENTRAOS_API_KEY,
      port: PORT,
    });
    this.setupWebviewRoutes();
  }


  /**
   * Handle new session creation and button press events
   */
  protected async onSession(session: AppSession, sessionId: string, userId: string): Promise<void> {
    // this gets called whenever a user launches the app
    this.logger.info(`Session started for user ${userId}`);

    // set the initial state of the user
    this.isStreamingPhotos.set(userId, false);
    this.nextPhotoTime.set(userId, Date.now());

    // Welcome message for voice commands
    await session.audio.speak("Say 'start streaming' to begin, 'stop streaming' to end, or 'help' for hints.", {
      voice_settings: {
        stability: 0.7,
        similarity_boost: 0.8,
        style: 0.3,
        speed: 0.9
      }
    });

    // Track processing state to prevent loops
    let isProcessingCommand = false;

    // Listen for voice commands via transcription
    const unsubscribe = session.events.onTranscription(async (data) => {
      // Only process final transcriptions to avoid partial commands
      if (!data.isFinal || isProcessingCommand) return;

      const command = data.text.toLowerCase().trim();
      
      // Skip empty commands or very short commands that might be noise
      if (!command || command.length < 3) return;

      // Filter out ambient noise and non-command speech
      const validCommands = ["start streaming", "stop streaming", "give hint", "hint", "help"];
      const isValidCommand = validCommands.some(cmd => command.includes(cmd));
      
      // Only process if it contains actual command keywords
      if (!isValidCommand) {
        this.logger.debug(`Ignoring non-command speech: "${command}"`);
        return;
      }

      this.logger.info(`Voice command received: "${command}"`);
      
      // Set processing flag to prevent concurrent processing
      isProcessingCommand = true;

      try {
        if (command.includes("start streaming")) {
          // Voice command to start streaming mode
          this.isStreamingPhotos.set(userId, true);
          this.logger.info(`Streaming mode started via voice for user ${userId}`);
          session.layouts.showTextWall("Streaming mode activated", {durationMs: 3000});
          await session.audio.speak("Streaming mode activated. Photos will be taken automatically.", {
            voice_settings: {
              stability: 0.7,
              similarity_boost: 0.8,
              style: 0.3,
              speed: 0.9
            }
          });
        } else if (command.includes("stop streaming")) {
          // Voice command to stop streaming mode
          this.isStreamingPhotos.set(userId, false);
          this.logger.info(`Streaming mode stopped via voice for user ${userId}`);
          session.layouts.showTextWall("Streaming mode deactivated", {durationMs: 3000});
          await session.audio.speak("Streaming mode deactivated.", {
            voice_settings: {
              stability: 0.7,
              similarity_boost: 0.8,
              style: 0.3,
              speed: 0.9
            }
          });
        } else if (command.includes("give hint") || command.includes("hint") || command.includes("help")) {
          session.layouts.showTextWall("Voice command: Giving hint...", {durationMs: 3000});
          try {
            // Call the give_hint endpoint with the user's command
            const response = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/give-hint`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                learned: command,
                question: command
              })
            });

            if (response.ok) {
              const result = await response.json();
              const hintText = result.hint || "Here's a hint to help you with your problem!";
              // Speak the hint response from the backend (strip markdown formatting for speech)
              const speechText = hintText.replace(/[*#`]/g, '').replace(/💡/g, '');
              await session.audio.speak(speechText, {
                voice_settings: {
                  stability: 0.7,
                  similarity_boost: 0.8,
                  style: 0.3,
                  speed: 0.9
                }
              });
            } else {
              await session.audio.speak("Sorry, I couldn't generate a hint right now.", {
                voice_settings: {
                  stability: 0.7,
                  similarity_boost: 0.8,
                  style: 0.3,
                  speed: 0.9
                }
              });
            }
          } catch (error) {
            this.logger.error(`Error getting hint: ${error}`);
            await session.audio.speak("Sorry, there was an error getting your hint.", {
              voice_settings: {
                stability: 0.7,
                similarity_boost: 0.8,
                style: 0.3,
                speed: 0.9
              }
            });
          }
        }
      } finally {
        // Reset processing flag after a delay to prevent rapid re-triggering
        setTimeout(() => {
          isProcessingCommand = false;
        }, 2000);
      }
    });

    // Clean up transcription listener when session ends
    this.addCleanupHandler(unsubscribe);

    // this gets called whenever a user presses a button
    session.events.onButtonPress(async (button) => {
      this.logger.info(`Button pressed: ${button.buttonId}, type: ${button.pressType}`);

      if (button.pressType === 'long') {
        // the user held the button, so we toggle the streaming mode
        this.isStreamingPhotos.set(userId, !this.isStreamingPhotos.get(userId));
        this.logger.info(`Streaming photos for user ${userId} is now ${this.isStreamingPhotos.get(userId)}`);
        return;
      } else {
        session.layouts.showTextWall("Button pressed, about to take photo", {durationMs: 4000});
        // the user pressed the button, so we take a single photo
        try {
          // first, get the photo
          const photo = await session.camera.requestPhoto();
          // if there was an error, log it
          this.logger.info(`Photo taken for user ${userId}, timestamp: ${photo.timestamp}`);
          this.cachePhoto(photo, userId);
        } catch (error) {
          this.logger.error(`Error taking photo: ${error}`);
        }
      }
    });

    // repeatedly check if we are in streaming mode and if we are ready to take another photo
    setInterval(async () => {
      if (this.isStreamingPhotos.get(userId) && Date.now() > (this.nextPhotoTime.get(userId) ?? 0)) {
        try {
          // set the next photos for 30 seconds from now, as a fallback if this fails
          this.nextPhotoTime.set(userId, Date.now() + 30000);

          // actually take the photo
          const photo = await session.camera.requestPhoto();

          // set the next photo time to now, since we are ready to take another photo
          this.nextPhotoTime.set(userId, Date.now());

          // cache the photo for display
          this.cachePhoto(photo, userId);
        } catch (error) {
          this.logger.error(`Error auto-taking photo: ${error}`);
        }
      }
    }, 1000);
  }

  protected async onStop(sessionId: string, userId: string, reason: string): Promise<void> {
    // clean up the user's state
    this.isStreamingPhotos.set(userId, false);
    this.nextPhotoTime.delete(userId);
    this.logger.info(`Session stopped for user ${userId}, reason: ${reason}`);
  }

  private async makeBackendRequest(photo: PhotoData, userId: string) {
    try {
      const base64Image = photo.buffer.toString('base64');
      const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
      
      const response = await fetch(`${backendUrl}/analyze-photo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: base64Image
        })
      });

      if (response.ok) {
        const ocrResult = await response.json();
        this.logger.info(`OCR analysis completed for user ${userId}: ${ocrResult.full_text}`);
        // You can store the OCR result or use it as needed
      } else {
        this.logger.error(`OCR analysis failed: ${response.statusText}`);
      }
    } catch (error) {
      this.logger.error(`Error sending photo to backend: ${error}`);
    }
  }
  
  /**
   * Cache a photo for display and send to backend for OCR analysis
   */
  private async cachePhoto(photo: PhotoData, userId: string) {
    // create a new stored photo object which includes the photo data and the user id
    const cachedPhoto: StoredPhoto = {
      requestId: photo.requestId,
      buffer: photo.buffer,
      timestamp: photo.timestamp,
      userId: userId,
      mimeType: photo.mimeType,
      filename: photo.filename,
      size: photo.size
    };

    // cache the photo for display
    this.photos.set(userId, cachedPhoto);
    // update the latest photo timestamp
    this.latestPhotoTimestamp.set(userId, cachedPhoto.timestamp.getTime());
    this.logger.info(`Photo cached for user ${userId}, timestamp: ${cachedPhoto.timestamp}`);

    // Send photo to backend for OCR analysis (fire and forget)
    this.makeBackendRequest(photo, userId).catch(error => {
      this.logger.error(`Backend request failed for user ${userId}:`, error);
    });
  }


  /**
   * Set up webview routes for photo display functionality
   */
  private setupWebviewRoutes(): void {
    const app = this.getExpressApp();

    // Serve static files from dist directory (built React app)
    app.use(express.static(path.join(process.cwd(), 'dist')));

    // Root route - serve React app
    app.get('/', (req: any, res: any) => {
      res.sendFile(path.join(process.cwd(), 'dist', 'index.html'));
    });

    // React chat route
    app.get('/react-chat', (req: any, res: any) => {
      res.sendFile(path.join(process.cwd(), 'dist', 'index.html'));
    });

    // API endpoint to get the latest photo for the authenticated user
    app.get('/api/latest-photo', (req: any, res: any) => {
      const userId = (req as AuthenticatedRequest).authUserId;

      if (!userId) {
        res.status(401).json({ error: 'Not authenticated' });
        return;
      }

      const photo = this.photos.get(userId);
      if (!photo) {
        res.status(404).json({ error: 'No photo available' });
        return;
      }

      res.json({
        requestId: photo.requestId,
        timestamp: photo.timestamp.getTime(),
        hasPhoto: true
      });
    });

    // API endpoint to get photo data
    app.get('/api/photo/:requestId', (req: any, res: any) => {
      const userId = (req as AuthenticatedRequest).authUserId;
      const requestId = req.params.requestId;

      if (!userId) {
        res.status(401).json({ error: 'Not authenticated' });
        return;
      }

      const photo = this.photos.get(userId);
      if (!photo || photo.requestId !== requestId) {
        res.status(404).json({ error: 'Photo not found' });
        return;
      }

      res.set({
        'Content-Type': photo.mimeType,
        'Cache-Control': 'no-cache'
      });
      res.send(photo.buffer);
    });

    // API endpoint to get current display text
    app.get('/api/display-text', (req: any, res: any) => {
      if (!this.displayText) {
        res.status(404).json({ error: 'No text available' });
        return;
      }

      res.json({
        text: this.displayText,
        timestamp: Date.now()
      });
    });

    // API endpoint to set display text
    app.post('/api/display-text', (req: any, res: any) => {
      const { text } = req.body;

      if (!text || typeof text !== 'string') {
        res.status(400).json({ error: 'Text is required and must be a string' });
        return;
      }

      this.displayText = text;
      res.json({ success: true, text: this.displayText });
    });

    // API endpoint for giving hints
    app.get('/api/get_hint', (req: any, res: any) => {
      if (!this.displayText) {
        res.status(404).json({ 
          success: false,
          error: 'No hint available at this time',
          timestamp: new Date().toISOString()
        });
        return;
      }

      res.json({ 
        success: true,
        hint: this.displayText,
        timestamp: new Date().toISOString()
      });
    });


    // Chat interface route
    app.get('/chat', async (req: any, res: any) => {
      const templatePath = path.join(process.cwd(), 'views', 'chat-interface.ejs');
      const html = await ejs.renderFile(templatePath, {});
      res.send(html);
    });

    // Main webview route - displays the photo viewer interface
    app.get('/webview', async (req: any, res: any) => {
      const userId = (req as AuthenticatedRequest).authUserId;

      if (!userId) {
        res.status(401).send(`
          <html>
            <head><title>Photo Viewer - Not Authenticated</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
              <h1>Please open this page from the MentraOS app</h1>
            </body>
          </html>
        `);
        return;
      }

      const templatePath = path.join(process.cwd(), 'views', 'photo-viewer.ejs');
      const html = await ejs.renderFile(templatePath, {});
      res.send(html);
    });
  }
}



// Start the server
// DEV CONSOLE URL: https://console.mentra.glass/
// Get your webhook URL from ngrok (or whatever public URL you have)
const app = new ExampleMentraOSApp();

app.start().catch(console.error);