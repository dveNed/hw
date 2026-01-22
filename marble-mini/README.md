# Marble Blast Mini

A mobile-first Marble Blast–style tilt/drag marble game that runs in the browser. Navigate your marble through obstacles, avoid holes, and reach the finish pad!

## Features

- **Touch Controls**: Drag anywhere on screen to tilt the board
- **Gyroscope Support**: Optional device tilt controls (toggle in settings)
- **3 Levels**: Increasing difficulty with unique layouts
- **Physics Engine**: Smooth velocity, friction, and collision response
- **Best Times**: Track your fastest completion for each level (stored locally)
- **Mobile-Optimized**: 60fps target, responsive design, works on iPhone Safari
- **No Dependencies**: Pure vanilla JavaScript, HTML, and CSS

## Game Elements

- **Marble**: Your player - guide it to the finish!
- **Bumpers** (pink/yellow circles): Bounce off these with extra force
- **Holes** (black circles): Fall in and reset with a 2-second penalty
- **Finish Pad** (blue circle): Reach this to complete the level
- **Walls** (white lines): Solid boundaries and obstacles

## Controls

### Touch Drag (Primary)
- Touch and drag anywhere on the screen
- Drag direction = tilt direction
- Longer drag = more tilt force
- Release to stop tilting

### Gyroscope (Optional)
1. Go to Settings
2. Enable "Use Gyroscope"
3. Grant permission when prompted (iOS)
4. Tilt your device to control the marble

### Other Controls
- **Pause Button** (⏸): Pause the game
- **Reset Level**: Restart current level from pause menu
- **Quit to Menu**: Return to level select

## How to Run Locally

1. **Clone or download** this repository

2. **Serve the files** using any static file server:

   **Option A - Python (if installed):**
   ```bash
   cd marble-mini
   python3 -m http.server 8000
   ```
   Then open: http://localhost:8000

   **Option B - Node.js (if installed):**
   ```bash
   cd marble-mini
   npx serve
   ```

   **Option C - VS Code:**
   - Install "Live Server" extension
   - Right-click `index.html` → "Open with Live Server"

3. **Test on mobile**:
   - Find your computer's local IP (e.g., 192.168.1.x)
   - On your phone's browser, visit: http://YOUR_IP:8000
   - Make sure phone and computer are on same WiFi network

## How to Deploy to GitHub Pages

### Method 1: GitHub Settings (Recommended)

1. **Push to GitHub**:
   ```bash
   git add marble-mini/
   git commit -m "Add Marble Blast Mini game"
   git push origin your-branch-name
   ```

2. **Enable GitHub Pages**:
   - Go to your repository on GitHub
   - Click **Settings** → **Pages**
   - Under "Source", select your branch (e.g., `main` or `claude/marble-blast-mobile-V2KTG`)
   - Under "Folder", select **/ (root)**
   - Click **Save**

3. **Access your game**:
   - Your game will be live at: `https://USERNAME.github.io/REPO-NAME/marble-mini/`
   - GitHub will show the URL in Settings → Pages
   - Wait 1-2 minutes for first deployment

### Method 2: Dedicated gh-pages Branch

1. **Create and switch to gh-pages branch**:
   ```bash
   git checkout -b gh-pages
   ```

2. **Move marble-mini contents to root** (optional for cleaner URLs):
   ```bash
   mv marble-mini/* .
   git add .
   git commit -m "Deploy to GitHub Pages"
   git push origin gh-pages
   ```

3. **Configure Pages**:
   - Go to Settings → Pages
   - Select `gh-pages` branch
   - Your game will be at: `https://USERNAME.github.io/REPO-NAME/`

## Mobile Testing Checklist

When testing on your phone, verify:

- ✅ Touch drag moves marble smoothly
- ✅ Marble bounces off walls (no tunneling)
- ✅ Bumpers provide extra bounce
- ✅ Holes reset the marble
- ✅ Finish pad completes level and shows time
- ✅ Best times persist after refresh
- ✅ Level switching works
- ✅ Pause/resume functions correctly
- ✅ Rotation doesn't break layout
- ✅ 60fps smooth performance (no jank)

## Level Descriptions

### Level 1: Getting Started
Simple introduction with basic obstacles. Learn the controls and physics.

### Level 2: The Gauntlet
Navigate through vertical corridors with precisely placed hazards. Timing is key!

### Level 3: Spiral Maze
Work your way through a spiral path to the center. Tight spaces and tricky turns.

## Browser Compatibility

**Tested and optimized for:**
- iOS Safari (iPhone/iPad)
- Chrome Mobile (Android)
- Desktop browsers (Chrome, Firefox, Safari, Edge)

**Note on Gyroscope:**
- iOS requires user permission (iOS 13+)
- Not all devices have gyroscope hardware
- Falls back to touch controls seamlessly

## Performance Notes

- Game loop targets 60fps
- Delta time is capped to prevent physics explosions
- Canvas uses device pixel ratio for crisp rendering
- Automatic scaling for different screen sizes
- Handles orientation changes dynamically

## Customization

Want to tweak the game? Edit `main.js`:

- **CONFIG object** (lines 2-12): Adjust physics constants
- **LEVELS array** (lines 15-100): Modify or add levels
- **Colors**: Search for hex codes in `main.js` and `style.css`

Example - Make it harder:
```javascript
const CONFIG = {
    MARBLE_RADIUS: 12,      // Smaller marble
    GRAVITY: 800,           // Stronger tilt effect
    FRICTION: 0.99,         // Less friction = harder control
    HOLE_RADIUS: 25,        // Bigger holes
    // ...
};
```

## Troubleshooting

**Game won't load:**
- Check browser console for errors (F12)
- Ensure files are served via HTTP/HTTPS (not file://)

**Gyroscope not working on iOS:**
- Must be HTTPS (or localhost)
- User must grant permission
- Some older devices lack gyroscope

**Physics feels weird:**
- Try different GRAVITY and FRICTION values in CONFIG
- Ensure dt capping is working (check for lag spikes)

**Touch controls not responding:**
- Check if another element is blocking touch events
- Try on actual device (not just emulator)

## License

Free to use and modify. Built as a demo project.

## Credits

Created with vanilla JavaScript - no frameworks or libraries used!
