// FAQ Toggle
document.querySelectorAll('.faq-item h3').forEach((item) => {
    item.addEventListener('click', () => {
        const content = item.nextElementSibling;
        content.style.display = content.style.display === 'block' ? 'none' : 'block';
    });
});
