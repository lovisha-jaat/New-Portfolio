/**
 * Portfolio animations — scroll reveals, hero effects, accessibility
 */
(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isMobile = window.innerWidth <= 768;

    /* ── Navbar scroll shadow ── */
    function initNavbarScroll() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        function updateNav() {
            navbar.classList.toggle('navbar-scrolled', window.scrollY > 20);
        }

        updateNav();
        window.addEventListener('scroll', updateNav, { passive: true });
    }

    /* ── Active nav link ── */
    function initActiveNavLink() {
        const links = document.querySelectorAll('.nav-links a');
        const path = window.location.pathname;

        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href === path || (path === '/' && href === '/')) {
                link.classList.add('active');
            }
        });
    }

    /* ── Smooth scroll for anchor links ── */
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth' });
                }
            });
        });
    }

    /* ── Scroll reveal (Intersection Observer) ── */
    function initScrollReveal() {
        const elements = document.querySelectorAll(
            '.fade-in, .slide-up, .reveal-up, .timeline-item, .timeline-card-wrapper, .animate-slide-up, .animate-fade-in'
        );

        if (prefersReducedMotion) {
            elements.forEach(el => el.classList.add('is-visible'));
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
        );

        elements.forEach(el => observer.observe(el));
    }

    /* ── Hero photo 3D tilt ── */
    function initHeroTilt() {
        if (prefersReducedMotion || isTouchDevice || isMobile) return;

        const container = document.querySelector('.hero-image-container');
        const frame = document.querySelector('.profile-image-frame');
        const orbBg = document.querySelector('.hero-photo-orb');
        if (!container || !frame) return;

        let rafId = null;

        function onMove(e) {
            if (rafId) cancelAnimationFrame(rafId);
            rafId = requestAnimationFrame(() => {
                const rect = container.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width - 0.5;
                const y = (e.clientY - rect.top) / rect.height - 0.5;
                const rotateX = y * -10;
                const rotateY = x * 10;

                frame.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;

                if (orbBg) {
                    orbBg.style.transform = `translate(${x * 22}px, ${y * 22}px) rotate(${x * 15}deg)`;
                }
            });
        }

        function onLeave() {
            frame.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg)';
            if (orbBg) orbBg.style.transform = '';
        }

        container.addEventListener('mousemove', onMove, { passive: true });
        container.addEventListener('mouseleave', onLeave);

        window.addEventListener('beforeunload', () => {
            container.removeEventListener('mousemove', onMove);
            container.removeEventListener('mouseleave', onLeave);
            if (rafId) cancelAnimationFrame(rafId);
        });
    }

    /* ── Hero role text typing animation ── */
    function initRoleTextRotation() {
        const el = document.getElementById('role-text');
        if (!el) return;

        const roles = [
            'Full Stack Developer',
            'AI/ML Enthusiast',
            'Python Developer',
            'Data Analytics Learner'
        ];

        if (prefersReducedMotion) {
            el.textContent = roles[0];
            return;
        }

        el.classList.add('typing-cursor');

        let index = 0;
        let charIndex = 0;
        let isDeleting = false;
        let pauseTimer = null;

        function tick() {
            const current = roles[index];

            if (!isDeleting) {
                el.textContent = current.substring(0, charIndex + 1);
                charIndex++;

                if (charIndex === current.length) {
                    pauseTimer = setTimeout(() => { isDeleting = true; tick(); }, 2200);
                    return;
                }
            } else {
                el.textContent = current.substring(0, charIndex - 1);
                charIndex--;

                if (charIndex === 0) {
                    isDeleting = false;
                    index = (index + 1) % roles.length;
                    pauseTimer = setTimeout(tick, 400);
                    return;
                }
            }

            const speed = isDeleting ? 35 : 65;
            pauseTimer = setTimeout(tick, speed);
        }

        tick();

        window.addEventListener('beforeunload', () => {
            if (pauseTimer) clearTimeout(pauseTimer);
        });
    }

    /* ── Developer character eye tracking ── */
    function initDevCharacterEyes() {
        const character = document.getElementById('dev-character');
        if (!character || prefersReducedMotion || isTouchDevice) return;

        function movePupils(e) {
            character.querySelectorAll('.eye').forEach((eye) => {
                const pupil = eye.querySelector('.pupil');
                if (!pupil) return;
                const rect = eye.getBoundingClientRect();
                const eyeX = rect.left + rect.width / 2;
                const eyeY = rect.top + rect.height / 2;
                const angle = Math.atan2(e.clientY - eyeY, e.clientX - eyeX);
                const dist = Math.min(4, Math.hypot(e.clientX - eyeX, e.clientY - eyeY) / 40);
                const x = Math.cos(angle) * dist;
                const y = Math.sin(angle) * dist;
                pupil.style.transform = `translate(${x}px, ${y}px)`;
            });
        }

        document.addEventListener('mousemove', movePupils, { passive: true });
        window.addEventListener('beforeunload', () => {
            document.removeEventListener('mousemove', movePupils);
        });
    }

    /* ── Magnetic buttons ── */
    function initMagneticButtons() {
        if (prefersReducedMotion || isTouchDevice) return;

        document.querySelectorAll('.btn, .magnetic-hover').forEach(btn => {
            btn.addEventListener('mousemove', function (e) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                this.style.transform = `translate(${x * 0.18}px, ${y * 0.18}px)`;
            });

            btn.addEventListener('mouseleave', function () {
                this.style.transform = '';
            });
        });
    }

    /* ── Skill bar animation ── */
    function initSkillBars() {
        const bars = document.querySelectorAll('.skill-bar-fill');
        if (!bars.length) return;

        if (prefersReducedMotion) {
            bars.forEach(bar => { bar.style.width = bar.dataset.width || '100%'; });
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const bar = entry.target;
                        bar.style.width = bar.dataset.width || '100%';
                        observer.unobserve(bar);
                    }
                });
            },
            { threshold: 0.5 }
        );

        bars.forEach(bar => observer.observe(bar));
    }

    /* ── Section heading underline animation ── */
    function initHeadingUnderlines() {
        document.querySelectorAll('.section-title, .page-title').forEach(title => {
            if (!title.querySelector('.title-underline')) {
                const underline = document.createElement('span');
                underline.className = 'title-underline';
                title.appendChild(underline);
            }
        });
    }

    /* ── Init on DOM ready ── */
    function init() {
        initNavbarScroll();
        initActiveNavLink();
        initSmoothScroll();
        initScrollReveal();
        initHeroTilt();
        initRoleTextRotation();
        initDevCharacterEyes();
        initMagneticButtons();
        initSkillBars();
        initHeadingUnderlines();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
