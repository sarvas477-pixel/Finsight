// ============================================
// CUSTOM CURSOR TRACKING
// ============================================

const cursor = document.querySelector('.cursor');
const cursorDot = document.querySelector('.cursor-dot');
let mouseX = 0;
let mouseY = 0;
let cursorX = 0;
let cursorY = 0;

document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;

    // Smooth cursor follow with delay
    cursorX += (mouseX - cursorX) * 0.2;
    cursorY += (mouseY - cursorY) * 0.2;

    cursor.style.left = cursorX + 'px';
    cursor.style.top = cursorY + 'px';

    cursorDot.style.left = mouseX + 'px';
    cursorDot.style.top = mouseY + 'px';

    // Update particles based on cursor position
    updateParticles(mouseX, mouseY);
});

// ============================================
// PARTICLE SYSTEM FOR MOTION GRAPHICS
// ============================================

const canvas = document.getElementById('particle-canvas');
const ctx = canvas.getContext('2d');

// Set canvas size
function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// Particle class
class Particle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.vx = (Math.random() - 0.5) * 4;
        this.vy = (Math.random() - 0.5) * 4 - 2;
        this.size = Math.random() * 3 + 0.5;
        this.opacity = Math.random() * 0.5 + 0.3;
        this.life = 100;
        this.maxLife = 100;
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.vy += 0.1; // gravity
        this.life -= 1;
        this.opacity = (this.life / this.maxLife) * (Math.random() * 0.5 + 0.3);
    }

    draw() {
        ctx.fillStyle = `rgba(167, 139, 250, ${this.opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();

        // Glow effect
        ctx.strokeStyle = `rgba(167, 139, 250, ${this.opacity * 0.5})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
    }
}

const particles = [];
let particleEmitCounter = 0;

function updateParticles(x, y) {
    // Emit particles near cursor
    if (particleEmitCounter++ % 2 === 0) {
        for (let i = 0; i < 2; i++) {
            particles.push(new Particle(
                x + (Math.random() - 0.5) * 20,
                y + (Math.random() - 0.5) * 20
            ));
        }
    }

    // Update and remove dead particles
    for (let i = particles.length - 1; i >= 0; i--) {
        particles[i].update();
        if (particles[i].life <= 0) {
            particles.splice(i, 1);
        }
    }
}

// Draw background particles continuously
function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    particles.forEach(particle => {
        particle.draw();
    });

    requestAnimationFrame(drawParticles);
}

drawParticles();

// ============================================
// TAB NAVIGATION
// ============================================

const navLinks = document.querySelectorAll('.nav-link');
const tabContents = document.querySelectorAll('.tab-content');

navLinks.forEach(link => {
    link.addEventListener('click', () => {
        const tabName = link.getAttribute('data-tab');

        // Remove active class from all contents and links
        tabContents.forEach(content => {
            content.classList.remove('active');
        });
        navLinks.forEach(l => {
            l.style.background = 'transparent';
            l.style.borderColor = 'rgba(167, 139, 250, 0.3)';
        });

        // Add active class to selected tab
        document.getElementById(tabName).classList.add('active');
        link.style.background = 'rgba(167, 139, 250, 0.2)';
        link.style.borderColor = 'rgba(167, 139, 250, 0.8)';
        link.style.boxShadow = '0 0 20px rgba(167, 139, 250, 0.5)';
    });
});

// ============================================
// INTERACTIVE CURSOR GLOW ON CARDS
// ============================================

const glassCards = document.querySelectorAll('.glass-card');

glassCards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Create glow effect based on cursor position
        card.style.background = `
            radial-gradient(
                600px at ${x}px ${y}px,
                rgba(167, 139, 250, 0.1),
                rgba(255, 255, 255, 0.08)
            )
        `;

        // Add border glow
        card.style.boxShadow = `
            0 0 40px rgba(167, 139, 250, 0.3),
            inset 0 0 40px rgba(167, 139, 250, 0.05)
        `;
    });

    card.addEventListener('mouseleave', () => {
        card.style.background = 'rgba(255, 255, 255, 0.08)';
        card.style.boxShadow = '0 8px 32px rgba(167, 139, 250, 0.2)';
    });
});

// ============================================
// BUTTON INTERACTION
// ============================================

const buttons = document.querySelectorAll('.glass-button');

buttons.forEach(button => {
    button.addEventListener('click', () => {
        // Create ripple effect
        const rect = button.getBoundingClientRect();
        const ripple = document.createElement('span');
        ripple.style.position = 'absolute';
        ripple.style.borderRadius = '50%';
        ripple.style.background = 'rgba(255, 255, 255, 0.5)';
        ripple.style.width = '20px';
        ripple.style.height = '20px';
        ripple.style.pointerEvents = 'none';
        ripple.style.animation = 'ripple 0.6s ease-out';

        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    });
});

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ============================================
// SMOOTH BACKGROUND ANIMATION
// ============================================

// Continuous floating animation for background elements
const spheres = document.querySelectorAll('.gradient-sphere');

// Add random initial delays
spheres.forEach((sphere, index) => {
    sphere.style.animationDelay = `${index * 0.5}s`;
});

// ============================================
// FORM INPUT FOCUS EFFECTS
// ============================================

const inputs = document.querySelectorAll('input, select, textarea');

inputs.forEach(input => {
    input.addEventListener('focus', () => {
        input.style.transform = 'scale(1.02)';
        input.style.background = 'rgba(255, 255, 255, 0.12)';
    });

    input.addEventListener('blur', () => {
        input.style.transform = 'scale(1)';
        input.style.background = 'rgba(255, 255, 255, 0.05)';
    });
});

// ============================================
// SCROLL ANIMATIONS
// ============================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe cards for fade-in animation
glassCards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'all 0.6s ease-out';
    observer.observe(card);
});

// ============================================
// PERFORMANCE OPTIMIZATION
// ============================================

let ticking = false;

// Throttle expensive operations
function throttle(func, limit) {
    return function() {
        if (!ticking) {
            func.apply(this, arguments);
            ticking = true;
            setTimeout(() => {
                ticking = false;
            }, limit);
        }
    };
}

// Throttle resize event
window.addEventListener('resize', throttle(resizeCanvas, 100));

// ============================================
// INITIAL PAGE ANIMATIONS
// ============================================

window.addEventListener('load', () => {
    // Animate elements on load
    const header = document.querySelector('.header');
    const tabPanel = document.querySelector('.tab-panel');

    if (header) header.style.animation = 'slideInDown 0.6s ease-out';
    if (tabPanel) tabPanel.style.animation = 'fadeInUp 0.8s ease-out 0.3s both';

    // Activate first tab
    if (navLinks.length > 0) {
        navLinks[0].click();
    }
});

// ============================================
// ACCESSIBILITY - KEYBOARD NAVIGATION
// ============================================

document.addEventListener('keydown', (e) => {
    const currentActive = document.querySelector('.tab-content.active');
    const currentIndex = Array.from(tabContents).indexOf(currentActive);

    if (e.key === 'ArrowRight') {
        const nextIndex = (currentIndex + 1) % navLinks.length;
        navLinks[nextIndex].click();
    } else if (e.key === 'ArrowLeft') {
        const prevIndex = (currentIndex - 1 + navLinks.length) % navLinks.length;
        navLinks[prevIndex].click();
    }
});

console.log('✨ FinSight Frontend Loaded Successfully!');
