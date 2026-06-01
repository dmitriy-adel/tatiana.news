// пользовательское соглашение
document.addEventListener('DOMContentLoaded', () => {
    const contentContainer = document.getElementById('content');
    const links = document.querySelectorAll('.toc-link');

    links.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                const headerOffset = 180;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + contentContainer.scrollTop - headerOffset;

                contentContainer.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    function highlightActiveSection() {
        let current = '';
        const sections = document.querySelectorAll('.section-header');

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (contentContainer.scrollTop >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });

        links.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    }

    contentContainer.addEventListener('scroll', highlightActiveSection);
    setTimeout(highlightActiveSection, 100);
});
