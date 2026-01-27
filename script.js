// ============================================
// ENTRY SCREEN
// ============================================
function enterSite() {
  const entryScreen = document.getElementById('entry-screen');
  document.body.classList.remove('entry-active');
  entryScreen.classList.add('hidden');
  document.body.style.overflow = 'auto';
  
  setTimeout(() => {
    entryScreen.style.display = 'none';
  }, 1000);
}

// Create floating particles for entry screen
function createOceanParticles() {
  const particlesContainer = document.getElementById('oceanParticles');
  if (!particlesContainer) return;

  const particleCount = 50;
  
  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.style.position = 'absolute';
    particle.style.width = Math.random() * 4 + 2 + 'px';
    particle.style.height = particle.style.width;
    particle.style.background = `rgba(78, 196, 196, ${Math.random() * 0.5 + 0.2})`;
    particle.style.borderRadius = '50%';
    particle.style.left = Math.random() * 100 + '%';
    particle.style.top = Math.random() * 100 + '%';
    particle.style.animation = `float ${Math.random() * 10 + 5}s ease-in-out infinite`;
    particle.style.animationDelay = Math.random() * 5 + 's';
    particlesContainer.appendChild(particle);
  }
}

// ============================================
// MAP SETUP - OCEANIC EARTH THEME WITH ZOOM (NO ROUTE LINES)
// ============================================
const map = L.map("map", {
  worldCopyJump: true,
  zoomControl: true,
  attributionControl: false,
  dragging: true,
  scrollWheelZoom: true,
  doubleClickZoom: true,
  touchZoom: true,
  minZoom: 2,
  maxZoom: 10
}).setView([20, 0], 2);

// Use Natural Earth tile layer for realistic Earth appearance
L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
  { 
    attribution: "",
    maxZoom: 10
  }
).addTo(map);

// Add topographic/land layer for green landmasses
L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  { 
    attribution: "",
    maxZoom: 10,
    opacity: 0.6
  }
).addTo(map);

// Custom styling for ocean blue and land green
const mapStyle = document.createElement('style');
mapStyle.textContent = `
  .leaflet-container {
    background: #1e5f8c !important;
  }
  .leaflet-tile-container {
    filter: saturate(1.3) brightness(0.9) contrast(1.1);
  }
`;
document.head.appendChild(mapStyle);

// Ship Icon with wave effect
const shipIcon = L.divIcon({
  className: "ship",
  html: "🚢",
  iconSize: [32, 32]
});

// Chapter coordinates based on the story
const chapters = [
  { name: "Port of Ostia", coords: [41.73, 12.29], unlocked: true },
  { name: "Signals in Cairo", coords: [30.0444, 31.2357], unlocked: true },
  { name: "Arabian Tides", coords: [20, 60], unlocked: false },
  { name: "Indian Abyss", coords: [-10, 80], unlocked: false },
  { name: "Philippine Sea", coords: [15, 130], unlocked: false },
  { name: "South Pacific", coords: [-21.694129, -147.915508], unlocked: false },
  { name: "North Pacific", coords: [40, -150], unlocked: false },
  { name: "Bering Sea", coords: [58, -175], unlocked: false },
  { name: "North Atlantic", coords: [45, -30], unlocked: false },
  { name: "Gulf of America", coords: [25, -90], unlocked: false },
  { name: "South Atlantic", coords: [-20, -30], unlocked: false },
  { name: "Return to Ostia", coords: [41.73, 12.29], unlocked: false }
];

// Create realistic ocean routes that avoid land (for ship animation only, no visible lines)
const oceanRoutes = [
  [[41.73, 12.29], [40.5, 14], [37, 18], [35, 23], [33, 28], [30.0444, 31.2357]],
  [[30.0444, 31.2357], [29, 33], [25, 36], [20, 40], [18, 50], [20, 60]],
  [[20, 60], [15, 65], [10, 70], [0, 75], [-10, 80]],
  [[-10, 80], [-8, 90], [-5, 100], [0, 110], [5, 120], [10, 125], [15, 130]],
  [[15, 130], [10, 140], [5, 150], [0, 160], [-5, 165], [-10, 170], [-15, 175], [-18, -175], [-21.694129, -147.915508]],
  [[-21.694129, -147.915508], [-15, -155], [-10, -160], [0, -165], [10, -165], [20, -162], [30, -158], [40, -150]],
  [[40, -150], [45, -155], [50, -165], [55, -172], [58, -175]],
  [[58, -175], [62, -170], [65, -160], [68, -145], [70, -120], [68, -95], [65, -75], [60, -60], [55, -50], [50, -40], [45, -30]],
  [[45, -30], [40, -35], [35, -45], [30, -60], [27, -75], [25, -82], [25, -90]],
  [[25, -90], [22, -85], [18, -75], [12, -65], [5, -50], [0, -45], [-10, -38], [-20, -30]],
  [[-20, -30], [-15, -20], [-10, -10], [0, 0], [10, 5], [20, 8], [30, 10], [36, 10], [39, 11], [41.73, 12.29]]
];

// Flatten all routes into one continuous path for ship animation
const route = oceanRoutes.flat();

// NO ROUTE LINES - Only chapter markers
// Add chapter markers with custom styling
chapters.forEach((chapter, index) => {
  const marker = L.circleMarker(chapter.coords, {
    radius: chapter.unlocked ? 12 : 8,
    fillColor: chapter.unlocked ? "#f4a836" : "#666",
    color: chapter.unlocked ? "#fff" : "#444",
    weight: 2,
    opacity: 1,
    fillOpacity: chapter.unlocked ? 0.9 : 0.5
  }).addTo(map);

  // Add pulse animation to unlocked markers
  if (chapter.unlocked) {
    const pulseMarker = L.circleMarker(chapter.coords, {
      radius: 12,
      fillColor: "#f4a836",
      color: "#f4a836",
      weight: 2,
      opacity: 0,
      fillOpacity: 0,
      className: 'pulse-marker'
    }).addTo(map);

    setInterval(() => {
      pulseMarker.setStyle({
        radius: 12,
        opacity: 0.6,
        fillOpacity: 0.3
      });
      setTimeout(() => {
        pulseMarker.setStyle({
          radius: 20,
          opacity: 0,
          fillOpacity: 0
        });
      }, 1000);
    }, 2000);
  }

  // Custom popup styling
  marker.bindPopup(`
    <div style="
      text-align: center; 
      padding: 1rem;
      background: linear-gradient(135deg, #0a2540 0%, #1e5f8c 100%);
      border: 2px solid #f4a836;
      color: #e8d4b8;
      min-width: 220px;
      border-radius: 8px;
    ">
      <strong style="
        color: #f4a836;
        font-size: 0.85rem;
        letter-spacing: 2px;
        display: block;
        margin-bottom: 0.5rem;
      ">CHAPTER ${String(index + 1).padStart(2, '0')}</strong>
      <span style="
        color: #e8d4b8;
        font-size: 1.2rem;
        font-weight: bold;
        display: block;
        margin-bottom: 0.8rem;
      ">${chapter.name}</span>
      <span style="
        font-size: 0.8rem;
        color: ${chapter.unlocked ? '#4ec4c4' : '#999'};
        font-weight: 700;
        letter-spacing: 1px;
        padding: 0.4rem 0.8rem;
        border-radius: 12px;
        background: ${chapter.unlocked ? 'rgba(78, 196, 196, 0.2)' : 'rgba(100, 100, 100, 0.2)'};
        border: 1px solid ${chapter.unlocked ? '#4ec4c4' : '#666'};
        display: inline-block;
      ">
        ${chapter.unlocked ? '✓ UNLOCKED' : '🔒 LOCKED'}
      </span>
    </div>
  `, {
    closeButton: false,
    className: 'custom-popup'
  });
});

// Animate ship along the route
const ship = L.marker(route[0], { icon: shipIcon }).addTo(map);

let currentSegment = 0;
let progress = 0;
const speed = 0.0003;

function animateShip() {
  const start = route[currentSegment];
  const end = route[currentSegment + 1];

  if (!end) {
    currentSegment = 0;
    progress = 0;
    requestAnimationFrame(animateShip);
    return;
  }

  const lat = start[0] + (end[0] - start[0]) * progress;
  const lng = start[1] + (end[1] - start[1]) * progress;

  ship.setLatLng([lat, lng]);

  progress += speed;

  if (progress >= 1) {
    progress = 0;
    currentSegment++;
  }

  requestAnimationFrame(animateShip);
}

animateShip();

// ============================================
// NAVIGATION SCROLL EFFECT
// ============================================
const nav = document.getElementById('main-nav');
let lastScroll = 0;

window.addEventListener('scroll', () => {
  const currentScroll = window.pageYOffset;

  if (currentScroll > 100) {
    nav.classList.add('scrolled');
  } else {
    nav.classList.remove('scrolled');
  }

  lastScroll = currentScroll;
});

// ============================================
// SMOOTH SCROLLING
// ============================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// ============================================
// TOKENOMICS MODAL
// ============================================
function openTokenomicsModal() {
  const modal = document.getElementById('tokenomics-modal');
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeTokenomicsModal() {
  const modal = document.getElementById('tokenomics-modal');
  modal.classList.remove('active');
  document.body.style.overflow = 'auto';
}

// ============================================
// WHITEPAPER MODAL
// ============================================
function openWhitepaperModal() {
  const modal = document.getElementById('whitepaper-modal');
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeWhitepaperModal() {
  const modal = document.getElementById('whitepaper-modal');
  modal.classList.remove('active');
  document.body.style.overflow = 'auto';
}

// ============================================
// WALLET MODAL
// ============================================
function openWalletModal() {
  const modal = document.getElementById('wallet-modal');
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeWalletModal() {
  const modal = document.getElementById('wallet-modal');
  modal.classList.remove('active');
  document.body.style.overflow = 'auto';
}

// Close modals on escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeTokenomicsModal();
    closeWhitepaperModal();
    closeWalletModal();
  }
});

// ============================================
// WALLET CONNECTION
// ============================================
async function connectWallet(walletType) {
  console.log(`Connecting to ${walletType}...`);

  if (typeof window.ethereum !== 'undefined') {
    try {
      const accounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts' 
      });
      
      const account = accounts[0];
      
      const walletBtn = document.querySelector('.wallet-connect-btn .nav-text');
      walletBtn.textContent = `${account.substring(0, 6)}...${account.substring(account.length - 4)}`;
      
      closeWalletModal();
      
      console.log('Connected wallet:', account);
      showNotification('Wallet Connected Successfully! 🌊');
      
    } catch (error) {
      console.error('Error connecting wallet:', error);
      showNotification('Failed to connect wallet. Please try again.', 'error');
    }
  } else {
    showNotification(`Please install ${walletType === 'metamask' ? 'MetaMask' : 'a Web3 wallet'} to connect!`, 'error');
    
    if (walletType === 'metamask') {
      setTimeout(() => {
        window.open('https://metamask.io/download/', '_blank');
      }, 1000);
    }
  }
}

// ============================================
// NOTIFICATION SYSTEM
// ============================================
function showNotification(message, type = 'success') {
  const existingNotif = document.querySelector('.notification');
  if (existingNotif) {
    existingNotif.remove();
  }

  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 5rem;
    right: 2rem;
    background: ${type === 'success' ? 'linear-gradient(135deg, #4ec4c4 0%, #2d8ca8 100%)' : 'linear-gradient(135deg, #ff6b6b 0%, #d97e3c 100%)'};
    color: white;
    padding: 1.2rem 2rem;
    border-radius: 8px;
    font-weight: 700;
    z-index: 10000;
    animation: slideIn 0.4s ease;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    border: 2px solid ${type === 'success' ? '#4ec4c4' : '#ff6b6b'};
  `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.4s ease';
    setTimeout(() => notification.remove(), 400);
  }, 3000);
}

const notificationStyle = document.createElement('style');
notificationStyle.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }

  .pulse-marker {
    transition: all 1s ease-out;
  }

  .leaflet-popup-content-wrapper {
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
  }

  .leaflet-popup-tip {
    display: none !important;
  }

  /* Custom Zoom Control Styling */
  .leaflet-control-zoom {
    border: 2px solid rgba(244, 168, 54, 0.3) !important;
    background: rgba(10, 37, 64, 0.9) !important;
    backdrop-filter: blur(10px);
    border-radius: 8px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
  }

  .leaflet-control-zoom a {
    background: transparent !important;
    color: #f4a836 !important;
    border: none !important;
    font-size: 20px !important;
    font-weight: bold !important;
    transition: all 0.3s ease !important;
    width: 36px !important;
    height: 36px !important;
    line-height: 36px !important;
  }

  .leaflet-control-zoom a:hover {
    background: rgba(244, 168, 54, 0.2) !important;
    color: #fff !important;
    transform: scale(1.1);
  }

  .leaflet-control-zoom-in {
    border-bottom: 1px solid rgba(244, 168, 54, 0.2) !important;
  }

  .leaflet-touch .leaflet-control-zoom {
    border-radius: 8px !important;
  }
`;
document.head.appendChild(notificationStyle);

// ============================================
// ENHANCED SCROLL ANIMATIONS
// ============================================
const scrollObserverOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -100px 0px'
};

const scrollObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      if (entry.target.classList.contains('chapter-card') || 
          entry.target.classList.contains('impact-item')) {
        entry.target.classList.add('visible');
      } else {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    }
  });
}, scrollObserverOptions);

// ============================================
// CHAPTER CARD HOVER EFFECTS
// ============================================
function initChapterCards() {
  const chapterCards = document.querySelectorAll('.chapter-card');
  
  chapterCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      const chapterNum = this.getAttribute('data-chapter');
      if (chapterNum) {
        const index = parseInt(chapterNum) - 1;
        if (chapters[index]) {
          map.setView(chapters[index].coords, 4, {
            animate: true,
            duration: 1
          });
        }
      }
    });
  });
}

// ============================================
// STATS COUNTER ANIMATION
// ============================================
function animateCounter(element, target, duration = 2000) {
  const originalText = element.textContent;
  const hasPlus = originalText.includes('+');
  const numTarget = parseInt(originalText.replace(/[^0-9]/g, ''));
  
  let start = 0;
  const increment = numTarget / (duration / 16);
  
  const timer = setInterval(() => {
    start += increment;
    if (start >= numTarget) {
      element.textContent = numTarget.toLocaleString() + (hasPlus ? '+' : '');
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(start).toLocaleString();
    }
  }, 16);
}

// ============================================
// CONSOLE MESSAGE
// ============================================
console.log('%c⚓ CAPTAIN GUIDO COIN ⚓', 'color: #f4a836; font-size: 28px; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);');
console.log('%c🌊 Saving our oceans, one token at a time', 'color: #4ec4c4; font-size: 16px; font-weight: bold;');
console.log('%c✓ Website loaded successfully!', 'color: #4ec4c4; font-size: 14px;');

// ============================================
// INITIALIZE ON PAGE LOAD
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  console.log('Captain Guido website initialized.');
  
  // Ensure body starts with entry screen active
  document.body.classList.add('entry-active');
  
  // Create ocean particles
  createOceanParticles();
  
  // Entry button
  const enterButton = document.getElementById('enterButton');
  if (enterButton) {
    enterButton.addEventListener('click', enterSite);
  }
  
  // Tokenomics modal buttons
  const openTokenomicsBtn = document.getElementById('openTokenomics');
  if (openTokenomicsBtn) {
    openTokenomicsBtn.addEventListener('click', openTokenomicsModal);
  }
  
  const closeTokenomicsBtn = document.getElementById('closeTokenomics');
  if (closeTokenomicsBtn) {
    closeTokenomicsBtn.addEventListener('click', closeTokenomicsModal);
  }

  const footerTokenomics = document.getElementById('footerTokenomics');
  if (footerTokenomics) {
    footerTokenomics.addEventListener('click', (e) => {
      e.preventDefault();
      openTokenomicsModal();
    });
  }
  
  // Whitepaper modal buttons
  const openWhitepaperBtn = document.getElementById('openWhitepaper');
  if (openWhitepaperBtn) {
    openWhitepaperBtn.addEventListener('click', openWhitepaperModal);
  }
  
  const closeWhitepaperBtn = document.getElementById('closeWhitepaper');
  if (closeWhitepaperBtn) {
    closeWhitepaperBtn.addEventListener('click', closeWhitepaperModal);
  }

  const footerWhitepaper = document.getElementById('footerWhitepaper');
  if (footerWhitepaper) {
    footerWhitepaper.addEventListener('click', (e) => {
      e.preventDefault();
      openWhitepaperModal();
    });
  }
  
  // Wallet connect button
  const walletConnectBtn = document.getElementById('walletConnectBtn');
  if (walletConnectBtn) {
    walletConnectBtn.addEventListener('click', openWalletModal);
  }
  
  // Close wallet modal button
  const closeWalletBtn = document.getElementById('closeWalletModal');
  if (closeWalletBtn) {
    closeWalletBtn.addEventListener('click', closeWalletModal);
  }
  
  // Modal overlays
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', () => {
      closeTokenomicsModal();
      closeWhitepaperModal();
      closeWalletModal();
    });
  });
  
  // Wallet options
  const walletOptions = document.querySelectorAll('.wallet-option');
  walletOptions.forEach(option => {
    option.addEventListener('click', function() {
      const walletType = this.getAttribute('data-wallet');
      connectWallet(walletType);
    });
  });

  // Initialize chapter card interactions
  initChapterCards();

  // Observe all cards for scroll animations
  const animatedElements = document.querySelectorAll(
    '.chapter-card, .impact-item, .section-content, .hero-content'
  );
  
  animatedElements.forEach(el => {
    scrollObserver.observe(el);
  });

  // Animate stats when they come into view
  const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const statValue = entry.target;
        animateCounter(statValue);
        statsObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.stat-value, .metric-value').forEach(stat => {
    statsObserver.observe(stat);
  });
});

// ============================================
// SMOOTH MAP FADE ON SCROLL
// ============================================
let ticking = false;

window.addEventListener('scroll', () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      const heroSection = document.getElementById('hero-map');
      const rect = heroSection.getBoundingClientRect();
      
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        const scrollPercent = Math.abs(rect.top) / window.innerHeight;
        const opacity = Math.max(0.3, 1 - scrollPercent);
        heroSection.style.opacity = opacity;
      }
      
      ticking = false;
    });
    
    ticking = true;
  }
});
