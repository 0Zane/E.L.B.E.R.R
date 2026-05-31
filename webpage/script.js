// Glitch effect interaction
const glitch = document.querySelector('.glitch');

document.addEventListener('mousemove', (e) => {
    const x = (e.clientX / window.innerWidth) * 100;
    const y = (e.clientY / window.innerHeight) * 100;
    
    glitch.style.setProperty('--x', x + '%');
    glitch.style.setProperty('--y', y + '%');
});

// Optional: Add cursor glow effect
document.addEventListener('mousemove', (e) => {
    const container = document.querySelector('.container');
    container.style.backgroundPosition = `${e.clientX / 20}px ${e.clientY / 20}px`;
});
