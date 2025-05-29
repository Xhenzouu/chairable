let currentIndex = 0;

function showSlides(index) {
    const slides = document.getElementsByClassName("slide");
    
    // Hide all slides
    for (let i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    
    // Show the current set of slides (3 slides at a time)
    for (let i = index * 3; i < index * 3 + 3 && i < slides.length; i++) {
        slides[i].style.display = "block";
    }

    // Update the current index
    currentIndex = index;
}

// Initialize the display of the first set of slides
showSlides(0);
