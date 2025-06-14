
// Typewriter effect
const typedTextElement = document.getElementById('typed-text');
const textToType = 'UltraRes';
let currentIndex = 0;

function typeText() {
    if (currentIndex < textToType.length) {
        typedTextElement.textContent += textToType[currentIndex];
        currentIndex++;
        setTimeout(typeText, 150);
    }
}

window.addEventListener('load', typeText);

// Image comparison slider functionality
const slider = document.getElementById('slider');
const blurOverlay = document.querySelector('.blur-overlay');
let isResizing = false;

slider.addEventListener('mousedown', startResizing);
document.addEventListener('mousemove', moveSlider);
document.addEventListener('mouseup', stopResizing);

slider.addEventListener('touchstart', startResizing);
document.addEventListener('touchmove', moveSlider);
document.addEventListener('touchend', stopResizing);

function startResizing(e) {
    isResizing = true;
    e.preventDefault();
}

function stopResizing() {
    isResizing = false;
}

function moveSlider(e) {
    if (!isResizing) return;

    const container = slider.parentElement;
    const rect = container.getBoundingClientRect();
    
    const pageX = e.pageX || (e.touches ? e.touches[0].pageX : 0);
    
    let position = (pageX - rect.left) / rect.width;
    position = Math.max(0, Math.min(1, position));
    
    slider.style.left = position * 100 + '%';
    blurOverlay.style.clipPath = `inset(0 ${100 - (position * 100)}% 0 0)`;
}

// Form handling
const form = document.getElementById('upscale-form');
const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const inputImage = document.getElementById('input-image');
const outputImage = document.getElementById('output-image');
const downloadButton = document.getElementById('download-button');

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        fileName.textContent = e.target.files[0].name;
        const reader = new FileReader();
        reader.onload = (e) => {
            inputImage.src = e.target.result;
            inputImage.classList.remove('hidden');
        };
        reader.readAsDataURL(e.target.files[0]);
    }
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = 'Upscaling...';

    try {
        const response = await fetch('/upscale', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upscaling failed');

        const data = await response.json();
        outputImage.src = `data:image/png;base64,${data.image}`;
        outputImage.classList.remove('hidden');
        downloadButton.classList.remove('hidden');
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during upscaling');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Upscale Image';
    }
});

downloadButton.addEventListener('click', () => {
    const link = document.createElement('a');
    link.href = outputImage.src;
    link.download = 'upscaled_image.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

document.querySelectorAll('.faq-question').forEach(question => {
        question.addEventListener('click', () => {
            const answer = question.nextElementSibling;
            const toggle = question.querySelector('.toggle');
            
            if (answer.style.display === 'block') {
                answer.style.display = 'none';
                toggle.textContent = '+';
            } else {
                answer.style.display = 'block';
                toggle.textContent = '-';
            }
        });
});


