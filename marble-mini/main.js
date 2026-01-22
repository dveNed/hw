// ===== GAME CONFIGURATION =====
const CONFIG = {
    MARBLE_RADIUS: 15,
    GRAVITY: 600,
    FRICTION: 0.98,
    BOUNCE: 0.7,
    MAX_VELOCITY: 800,
    HOLE_RADIUS: 20,
    BUMPER_RADIUS: 25,
    FINISH_RADIUS: 30,
    TARGET_FPS: 60,
    MAX_DT: 1/30
};

// ===== LEVEL DATA =====
const LEVELS = [
    {
        id: 1,
        name: "Getting Started",
        marble: { x: 50, y: 50 },
        finish: { x: 550, y: 450 },
        walls: [
            { x1: 0, y1: 0, x2: 600, y2: 0 },
            { x1: 600, y1: 0, x2: 600, y2: 500 },
            { x1: 600, y1: 500, x2: 0, y2: 500 },
            { x1: 0, y1: 500, x2: 0, y2: 0 },
            { x1: 200, y1: 100, x2: 400, y2: 100 },
            { x1: 150, y1: 300, x2: 450, y2: 300 }
        ],
        bumpers: [
            { x: 300, y: 200 },
            { x: 200, y: 400 },
            { x: 400, y: 400 },
            { x: 100, y: 200 },
            { x: 500, y: 250 }
        ],
        holes: [
            { x: 300, y: 250 },
            { x: 250, y: 400 },
            { x: 350, y: 150 }
        ]
    },
    {
        id: 2,
        name: "The Gauntlet",
        marble: { x: 50, y: 250 },
        finish: { x: 550, y: 250 },
        walls: [
            { x1: 0, y1: 0, x2: 600, y2: 0 },
            { x1: 600, y1: 0, x2: 600, y2: 500 },
            { x1: 600, y1: 500, x2: 0, y2: 500 },
            { x1: 0, y1: 500, x2: 0, y2: 0 },
            { x1: 150, y1: 0, x2: 150, y2: 200 },
            { x1: 150, y1: 300, x2: 150, y2: 500 },
            { x1: 300, y1: 0, x2: 300, y2: 200 },
            { x1: 300, y1: 300, x2: 300, y2: 500 },
            { x1: 450, y1: 0, x2: 450, y2: 200 },
            { x1: 450, y1: 300, x2: 450, y2: 500 }
        ],
        bumpers: [
            { x: 75, y: 100 },
            { x: 75, y: 400 },
            { x: 225, y: 250 },
            { x: 375, y: 100 },
            { x: 375, y: 400 },
            { x: 525, y: 250 }
        ],
        holes: [
            { x: 150, y: 250 },
            { x: 300, y: 250 },
            { x: 450, y: 250 }
        ]
    },
    {
        id: 3,
        name: "Spiral Maze",
        marble: { x: 300, y: 250 },
        finish: { x: 300, y: 50 },
        walls: [
            { x1: 0, y1: 0, x2: 600, y2: 0 },
            { x1: 600, y1: 0, x2: 600, y2: 500 },
            { x1: 600, y1: 500, x2: 0, y2: 500 },
            { x1: 0, y1: 500, x2: 0, y2: 0 },
            { x1: 100, y1: 100, x2: 500, y2: 100 },
            { x1: 500, y1: 100, x2: 500, y2: 400 },
            { x1: 500, y1: 400, x2: 100, y2: 400 },
            { x1: 100, y1: 400, x2: 100, y2: 200 },
            { x1: 100, y1: 200, x2: 400, y2: 200 },
            { x1: 400, y1: 200, x2: 400, y2: 300 },
            { x1: 200, y1: 300, x2: 400, y2: 300 }
        ],
        bumpers: [
            { x: 150, y: 150 },
            { x: 450, y: 150 },
            { x: 450, y: 350 },
            { x: 250, y: 350 },
            { x: 250, y: 250 }
        ],
        holes: [
            { x: 300, y: 150 },
            { x: 350, y: 250 },
            { x: 200, y: 350 },
            { x: 400, y: 350 }
        ]
    }
];

// ===== GAME STATE =====
class Game {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.running = false;
        this.paused = false;
        this.currentLevel = null;
        this.levelIndex = 0;

        this.marble = {
            x: 0,
            y: 0,
            vx: 0,
            vy: 0,
            radius: CONFIG.MARBLE_RADIUS
        };

        this.tilt = { x: 0, y: 0 };
        this.touchStart = null;
        this.useGyro = false;
        this.soundEnabled = true;

        this.timer = 0;
        this.bestTimes = this.loadBestTimes();

        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;

        this.setupCanvas();
        this.setupControls();
        this.setupUI();
        this.loadSettings();

        window.addEventListener('resize', () => this.setupCanvas());
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.setupCanvas(), 100);
        });
    }

    setupCanvas() {
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;

        // Reset transform before scaling to prevent compounding
        this.ctx.setTransform(1, 0, 0, 1, 0, 0);
        this.ctx.scale(dpr, dpr);

        // Calculate scaling to fit 600x500 game area
        const scaleX = rect.width / 600;
        const scaleY = rect.height / 500;
        this.scale = Math.min(scaleX, scaleY);

        this.offsetX = (rect.width - 600 * this.scale) / 2;
        this.offsetY = (rect.height - 500 * this.scale) / 2;
    }

    setupControls() {
        const overlay = document.getElementById('touch-overlay');

        overlay.addEventListener('touchstart', (e) => {
            if (this.paused) return;
            e.preventDefault();
            const touch = e.touches[0];
            this.touchStart = {
                x: touch.clientX,
                y: touch.clientY
            };
        }, { passive: false });

        overlay.addEventListener('touchmove', (e) => {
            if (this.paused || !this.touchStart) return;
            e.preventDefault();
            const touch = e.touches[0];
            const dx = touch.clientX - this.touchStart.x;
            const dy = touch.clientY - this.touchStart.y;

            const maxDistance = 100;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const clampedDistance = Math.min(distance, maxDistance);

            if (distance > 0) {
                this.tilt.x = (dx / distance) * (clampedDistance / maxDistance);
                this.tilt.y = (dy / distance) * (clampedDistance / maxDistance);
            }
        }, { passive: false });

        overlay.addEventListener('touchend', () => {
            this.touchStart = null;
            this.tilt = { x: 0, y: 0 };
        });

        // Gyroscope support
        if (window.DeviceOrientationEvent) {
            window.addEventListener('deviceorientation', (e) => {
                if (!this.useGyro || this.paused) return;

                const gamma = e.gamma || 0;  // Left-right tilt (-90 to 90)
                const beta = e.beta || 0;    // Front-back tilt (-180 to 180)

                this.tilt.x = Math.max(-1, Math.min(1, gamma / 45));
                this.tilt.y = Math.max(-1, Math.min(1, (beta - 45) / 45));
            });
        }
    }

    setupUI() {
        document.getElementById('start-btn').addEventListener('click', () => {
            this.showScreen('level-select-screen');
            this.updateLevelButtons();
        });

        document.getElementById('settings-btn').addEventListener('click', () => {
            this.showScreen('settings-screen');
        });

        document.getElementById('back-to-menu-btn').addEventListener('click', () => {
            this.showScreen('menu-screen');
        });

        document.getElementById('settings-back-btn').addEventListener('click', () => {
            this.showScreen('menu-screen');
        });

        document.getElementById('pause-btn').addEventListener('click', () => {
            this.pause();
        });

        document.getElementById('resume-btn').addEventListener('click', () => {
            this.resume();
        });

        document.getElementById('reset-level-btn').addEventListener('click', () => {
            this.resume();
            this.resetMarble();
        });

        document.getElementById('quit-btn').addEventListener('click', () => {
            this.stopGame();
            this.showScreen('level-select-screen');
        });

        document.getElementById('next-level-btn').addEventListener('click', () => {
            this.hideOverlay('complete-overlay');
            this.levelIndex++;
            if (this.levelIndex >= LEVELS.length) {
                this.levelIndex = 0;
            }
            this.startLevel(this.levelIndex);
        });

        document.getElementById('retry-btn').addEventListener('click', () => {
            this.hideOverlay('complete-overlay');
            this.startLevel(this.levelIndex);
        });

        document.getElementById('complete-quit-btn').addEventListener('click', () => {
            this.hideOverlay('complete-overlay');
            this.stopGame();
            this.showScreen('level-select-screen');
        });

        document.getElementById('gyro-toggle').addEventListener('change', (e) => {
            this.useGyro = e.target.checked;
            this.saveSettings();

            if (this.useGyro && typeof DeviceOrientationEvent.requestPermission === 'function') {
                DeviceOrientationEvent.requestPermission()
                    .then(permissionState => {
                        if (permissionState !== 'granted') {
                            this.useGyro = false;
                            e.target.checked = false;
                            alert('Gyroscope permission denied');
                        }
                    })
                    .catch(console.error);
            }
        });

        document.getElementById('sound-toggle').addEventListener('change', (e) => {
            this.soundEnabled = e.target.checked;
            this.saveSettings();
        });
    }

    updateLevelButtons() {
        const container = document.getElementById('level-buttons');
        container.innerHTML = '';

        LEVELS.forEach((level, index) => {
            const btn = document.createElement('button');
            btn.className = 'level-btn btn-medium';
            btn.innerHTML = `
                <div>Level ${level.id}</div>
                <div class="level-time">${this.bestTimes[level.id] ? this.formatTime(this.bestTimes[level.id]) : '--'}</div>
            `;
            btn.addEventListener('click', () => {
                this.startLevel(index);
            });
            container.appendChild(btn);
        });
    }

    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById(screenId).classList.remove('hidden');

        if (screenId === 'menu-screen') {
            this.updateBestTimesDisplay();
        }
    }

    showOverlay(overlayId) {
        document.getElementById(overlayId).classList.remove('hidden');
    }

    hideOverlay(overlayId) {
        document.getElementById(overlayId).classList.add('hidden');
    }

    startLevel(index) {
        this.levelIndex = index;
        this.currentLevel = LEVELS[index];
        this.resetMarble();
        this.timer = 0;
        this.running = true;
        this.paused = false;

        this.showScreen('game-screen');
        this.hideOverlay('pause-overlay');
        this.hideOverlay('complete-overlay');

        document.getElementById('level-name').textContent = this.currentLevel.name;

        this.lastTime = performance.now();
        requestAnimationFrame((t) => this.gameLoop(t));
    }

    stopGame() {
        this.running = false;
        this.paused = false;
    }

    pause() {
        this.paused = true;
        this.showOverlay('pause-overlay');
    }

    resume() {
        this.paused = false;
        this.hideOverlay('pause-overlay');
        this.lastTime = performance.now();
    }

    resetMarble() {
        this.marble.x = this.currentLevel.marble.x;
        this.marble.y = this.currentLevel.marble.y;
        this.marble.vx = 0;
        this.marble.vy = 0;
        this.tilt = { x: 0, y: 0 };
    }

    gameLoop(currentTime) {
        if (!this.running) return;

        let dt = (currentTime - this.lastTime) / 1000;
        this.lastTime = currentTime;

        // Cap dt to prevent physics issues
        dt = Math.min(dt, CONFIG.MAX_DT);

        if (!this.paused) {
            this.update(dt);
            this.timer += dt;
            document.getElementById('timer').textContent = this.formatTime(this.timer);
        }

        this.render();

        requestAnimationFrame((t) => this.gameLoop(t));
    }

    update(dt) {
        // Apply tilt as gravity
        const ax = this.tilt.x * CONFIG.GRAVITY;
        const ay = this.tilt.y * CONFIG.GRAVITY;

        // Update velocity
        this.marble.vx += ax * dt;
        this.marble.vy += ay * dt;

        // Apply friction
        this.marble.vx *= CONFIG.FRICTION;
        this.marble.vy *= CONFIG.FRICTION;

        // Clamp velocity
        const speed = Math.sqrt(this.marble.vx ** 2 + this.marble.vy ** 2);
        if (speed > CONFIG.MAX_VELOCITY) {
            this.marble.vx = (this.marble.vx / speed) * CONFIG.MAX_VELOCITY;
            this.marble.vy = (this.marble.vy / speed) * CONFIG.MAX_VELOCITY;
        }

        // Update position
        this.marble.x += this.marble.vx * dt;
        this.marble.y += this.marble.vy * dt;

        // Collision detection
        this.checkWallCollisions();
        this.checkBumperCollisions();
        this.checkHoleCollisions();
        this.checkFinishCollision();
    }

    checkWallCollisions() {
        this.currentLevel.walls.forEach(wall => {
            const closest = this.closestPointOnLine(
                this.marble.x, this.marble.y,
                wall.x1, wall.y1, wall.x2, wall.y2
            );

            const dx = this.marble.x - closest.x;
            const dy = this.marble.y - closest.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < this.marble.radius) {
                // Push marble out
                const overlap = this.marble.radius - distance;
                const nx = dx / distance;
                const ny = dy / distance;

                this.marble.x += nx * overlap;
                this.marble.y += ny * overlap;

                // Reflect velocity
                const dot = this.marble.vx * nx + this.marble.vy * ny;
                this.marble.vx = (this.marble.vx - 2 * dot * nx) * CONFIG.BOUNCE;
                this.marble.vy = (this.marble.vy - 2 * dot * ny) * CONFIG.BOUNCE;
            }
        });
    }

    checkBumperCollisions() {
        this.currentLevel.bumpers.forEach(bumper => {
            const dx = this.marble.x - bumper.x;
            const dy = this.marble.y - bumper.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const minDistance = this.marble.radius + CONFIG.BUMPER_RADIUS;

            if (distance < minDistance) {
                // Push marble out
                const overlap = minDistance - distance;
                const nx = dx / distance;
                const ny = dy / distance;

                this.marble.x += nx * overlap;
                this.marble.y += ny * overlap;

                // Reflect velocity with extra bounce
                const dot = this.marble.vx * nx + this.marble.vy * ny;
                this.marble.vx = (this.marble.vx - 2 * dot * nx) * 1.2;
                this.marble.vy = (this.marble.vy - 2 * dot * ny) * 1.2;
            }
        });
    }

    checkHoleCollisions() {
        this.currentLevel.holes.forEach(hole => {
            const dx = this.marble.x - hole.x;
            const dy = this.marble.y - hole.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < CONFIG.HOLE_RADIUS) {
                this.resetMarble();
                this.timer += 2; // Time penalty
            }
        });
    }

    checkFinishCollision() {
        const dx = this.marble.x - this.currentLevel.finish.x;
        const dy = this.marble.y - this.currentLevel.finish.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < CONFIG.FINISH_RADIUS) {
            this.completeLevel();
        }
    }

    completeLevel() {
        this.paused = true;

        const levelId = this.currentLevel.id;
        const currentTime = this.timer;
        const bestTime = this.bestTimes[levelId];

        if (!bestTime || currentTime < bestTime) {
            this.bestTimes[levelId] = currentTime;
            this.saveBestTimes();
            document.getElementById('complete-best').textContent = `🏆 New Best Time!`;
        } else {
            document.getElementById('complete-best').textContent = `Best: ${this.formatTime(bestTime)}`;
        }

        document.getElementById('complete-time').textContent = `Time: ${this.formatTime(currentTime)}`;

        // Hide Next Level button if on last level
        const nextBtn = document.getElementById('next-level-btn');
        if (this.levelIndex >= LEVELS.length - 1) {
            nextBtn.style.display = 'none';
        } else {
            nextBtn.style.display = 'block';
        }

        this.showOverlay('complete-overlay');
    }

    closestPointOnLine(px, py, x1, y1, x2, y2) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const length = dx * dx + dy * dy;

        if (length === 0) return { x: x1, y: y1 };

        let t = ((px - x1) * dx + (py - y1) * dy) / length;
        t = Math.max(0, Math.min(1, t));

        return {
            x: x1 + t * dx,
            y: y1 + t * dy
        };
    }

    render() {
        const ctx = this.ctx;
        const w = this.canvas.width / (window.devicePixelRatio || 1);
        const h = this.canvas.height / (window.devicePixelRatio || 1);

        // Clear
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, w, h);

        ctx.save();
        ctx.translate(this.offsetX, this.offsetY);
        ctx.scale(this.scale, this.scale);

        if (!this.currentLevel) {
            ctx.restore();
            return;
        }

        // Draw finish pad
        ctx.fillStyle = '#4facfe';
        ctx.beginPath();
        ctx.arc(this.currentLevel.finish.x, this.currentLevel.finish.y, CONFIG.FINISH_RADIUS, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#00f2fe';
        ctx.lineWidth = 4;
        ctx.stroke();

        // Draw holes
        ctx.fillStyle = '#000';
        this.currentLevel.holes.forEach(hole => {
            ctx.beginPath();
            ctx.arc(hole.x, hole.y, CONFIG.HOLE_RADIUS, 0, Math.PI * 2);
            ctx.fill();

            // Inner shadow effect
            const gradient = ctx.createRadialGradient(hole.x, hole.y, 0, hole.x, hole.y, CONFIG.HOLE_RADIUS);
            gradient.addColorStop(0, 'rgba(0,0,0,1)');
            gradient.addColorStop(1, 'rgba(50,50,50,0.5)');
            ctx.fillStyle = gradient;
            ctx.fill();
        });

        // Draw bumpers
        this.currentLevel.bumpers.forEach(bumper => {
            const gradient = ctx.createRadialGradient(bumper.x, bumper.y, 0, bumper.x, bumper.y, CONFIG.BUMPER_RADIUS);
            gradient.addColorStop(0, '#fa709a');
            gradient.addColorStop(1, '#fee140');
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(bumper.x, bumper.y, CONFIG.BUMPER_RADIUS, 0, Math.PI * 2);
            ctx.fill();
        });

        // Draw walls
        ctx.strokeStyle = '#f5f5f5';
        ctx.lineWidth = 8;
        ctx.lineCap = 'round';
        this.currentLevel.walls.forEach(wall => {
            ctx.beginPath();
            ctx.moveTo(wall.x1, wall.y1);
            ctx.lineTo(wall.x2, wall.y2);
            ctx.stroke();
        });

        // Draw marble with gradient
        const gradient = ctx.createRadialGradient(
            this.marble.x - 5, this.marble.y - 5, 2,
            this.marble.x, this.marble.y, this.marble.radius
        );
        gradient.addColorStop(0, '#fff');
        gradient.addColorStop(0.3, '#f093fb');
        gradient.addColorStop(1, '#f5576c');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.marble.x, this.marble.y, this.marble.radius, 0, Math.PI * 2);
        ctx.fill();

        // Marble highlight
        ctx.fillStyle = 'rgba(255,255,255,0.6)';
        ctx.beginPath();
        ctx.arc(this.marble.x - 5, this.marble.y - 5, 5, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
    }

    formatTime(seconds) {
        return seconds.toFixed(2) + 's';
    }

    loadBestTimes() {
        const stored = localStorage.getItem('marbleBlastBestTimes');
        return stored ? JSON.parse(stored) : {};
    }

    saveBestTimes() {
        localStorage.setItem('marbleBlastBestTimes', JSON.stringify(this.bestTimes));
        this.updateBestTimesDisplay();
        this.updateLevelButtons();
    }

    updateBestTimesDisplay() {
        const container = document.getElementById('best-times');
        if (Object.keys(this.bestTimes).length === 0) {
            container.innerHTML = '<div>No times yet - start playing!</div>';
            return;
        }

        let html = '<div style="margin-bottom: 10px; font-weight: 600;">Best Times</div>';
        LEVELS.forEach(level => {
            if (this.bestTimes[level.id]) {
                html += `<div>Level ${level.id}: ${this.formatTime(this.bestTimes[level.id])}</div>`;
            }
        });
        container.innerHTML = html;
    }

    loadSettings() {
        const gyroSetting = localStorage.getItem('marbleBlastGyro');
        const soundSetting = localStorage.getItem('marbleBlastSound');

        if (gyroSetting !== null) {
            this.useGyro = gyroSetting === 'true';
            document.getElementById('gyro-toggle').checked = this.useGyro;
        }

        if (soundSetting !== null) {
            this.soundEnabled = soundSetting === 'true';
            document.getElementById('sound-toggle').checked = this.soundEnabled;
        }
    }

    saveSettings() {
        localStorage.setItem('marbleBlastGyro', this.useGyro);
        localStorage.setItem('marbleBlastSound', this.soundEnabled);
    }
}

// ===== INITIALIZE =====
let game;

window.addEventListener('load', () => {
    game = new Game();
});
