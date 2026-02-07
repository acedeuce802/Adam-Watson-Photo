// Portfolio Carousel - Updated with Timer Reset on Arrow Click

const images = [
    'images/portfolio/image1.jpg',
    'images/portfolio/image2.jpg',
    // ... all 71 images
];

// Shuffle images
for (let i = images.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [images[i], images[j]] = [images[j], images[i]];
}

let currentIndex = 0;
let autoRotateInterval = null;

const carouselImage = document.getElementById('carousel-image');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');

function showImage(index) {
    carouselImage.src = images[index];
}

function nextImage() {
    currentIndex = (currentIndex + 1) % images.length;
    showImage(currentIndex);
}

function prevImage() {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    showImage(currentIndex);
}

function startAutoRotate() {
    // Clear any existing interval
    if (autoRotateInterval) {
        clearInterval(autoRotateInterval);
    }
    
    // Start new 5-second interval
    autoRotateInterval = setInterval(nextImage, 5000);
}

// Event listeners with timer reset
nextBtn.addEventListener('click', () => {
    nextImage();
    startAutoRotate(); // Reset the 5-second timer
});

prevBtn.addEventListener('click', () => {
    prevImage();
    startAutoRotate(); // Reset the 5-second timer
});

// Initial setup
showImage(currentIndex);
startAutoRotate();
