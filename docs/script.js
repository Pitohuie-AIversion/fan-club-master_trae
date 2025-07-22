// Smooth scrolling for navigation links
document.addEventListener('DOMContentLoaded', function() {
    // Get all navigation links
    const navLinks = document.querySelectorAll('.nav-menu a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Highlight active navigation item
    function highlightActiveNav() {
        const sections = document.querySelectorAll('section[id]');
        const scrollPos = window.scrollY + 100;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                // Remove active class from all nav links
                navLinks.forEach(link => {
                    link.classList.remove('active');
                });
                
                // Add active class to current section's nav link
                const activeLink = document.querySelector(`.nav-menu a[href="#${sectionId}"]`);
                if (activeLink) {
                    activeLink.classList.add('active');
                }
            }
        });
    }
    
    // Listen for scroll events
    window.addEventListener('scroll', highlightActiveNav);
    
    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe all sections and cards
    const animateElements = document.querySelectorAll('.section, .overview-card, .feature-item, .download-item');
    animateElements.forEach(el => {
        observer.observe(el);
    });
    
    // Add animation styles
    const style = document.createElement('style');
    style.textContent = `
        .animate-in {
            animation: slideInUp 0.6s ease-out forwards;
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .nav-menu a.active {
            opacity: 1;
            border-bottom: 2px solid white;
            padding-bottom: 2px;
        }
    `;
    document.head.appendChild(style);
    
    // Mobile menu toggle (if needed in future)
    function createMobileMenu() {
        const navbar = document.querySelector('.navbar');
        const navMenu = document.querySelector('.nav-menu');
        
        // Create hamburger button
        const hamburger = document.createElement('button');
        hamburger.className = 'hamburger';
        hamburger.innerHTML = '☰';
        hamburger.style.cssText = `
            display: none;
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
        `;
        
        // Add hamburger to nav container
        const navContainer = document.querySelector('.nav-container');
        navContainer.appendChild(hamburger);
        
        // Toggle mobile menu
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('mobile-active');
        });
        
        // Mobile styles
        const mobileStyle = document.createElement('style');
        mobileStyle.textContent = `
            @media (max-width: 768px) {
                .hamburger {
                    display: block !important;
                }
                
                .nav-menu {
                    display: none;
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: rgba(102, 126, 234, 0.95);
                    flex-direction: column;
                    padding: 1rem;
                    backdrop-filter: blur(10px);
                }
                
                .nav-menu.mobile-active {
                    display: flex;
                }
                
                .nav-menu a {
                    padding: 0.5rem 0;
                    border-bottom: 1px solid rgba(255,255,255,0.2);
                }
                
                .nav-menu a:last-child {
                    border-bottom: none;
                }
            }
        `;
        document.head.appendChild(mobileStyle);
    }
    
    createMobileMenu();
    
    // Copy code functionality
    function addCopyButtons() {
        const codeBlocks = document.querySelectorAll('pre code');
        
        codeBlocks.forEach(codeBlock => {
            const pre = codeBlock.parentElement;
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-btn';
            copyButton.textContent = '复制';
            copyButton.style.cssText = `
                position: absolute;
                top: 10px;
                right: 10px;
                background: #667eea;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.8rem;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            
            pre.style.position = 'relative';
            pre.appendChild(copyButton);
            
            // Show button on hover
            pre.addEventListener('mouseenter', () => {
                copyButton.style.opacity = '1';
            });
            
            pre.addEventListener('mouseleave', () => {
                copyButton.style.opacity = '0';
            });
            
            // Copy functionality
            copyButton.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(codeBlock.textContent);
                    copyButton.textContent = '已复制!';
                    copyButton.style.background = '#28a745';
                    
                    setTimeout(() => {
                        copyButton.textContent = '复制';
                        copyButton.style.background = '#667eea';
                    }, 2000);
                } catch (err) {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = codeBlock.textContent;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    
                    copyButton.textContent = '已复制!';
                    copyButton.style.background = '#28a745';
                    
                    setTimeout(() => {
                        copyButton.textContent = '复制';
                        copyButton.style.background = '#667eea';
                    }, 2000);
                }
            });
        });
    }
    
    addCopyButtons();
    
    // Parallax effect for hero section
    function addParallaxEffect() {
        const hero = document.querySelector('.hero');
        if (!hero) return;
        
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            hero.style.transform = `translateY(${rate}px)`;
        });
    }
    
    addParallaxEffect();
    
    // Typing animation for hero title
    function addTypingAnimation() {
        const title = document.querySelector('.hero-content h1');
        if (!title) return;
        
        const text = title.textContent;
        title.textContent = '';
        title.style.borderRight = '2px solid white';
        
        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                title.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            } else {
                // Remove cursor after typing is complete
                setTimeout(() => {
                    title.style.borderRight = 'none';
                }, 1000);
            }
        };
        
        // Start typing animation after a short delay
        setTimeout(typeWriter, 500);
    }
    
    // Uncomment to enable typing animation
    // addTypingAnimation();
    
    // Counter animation for statistics
    function animateCounters() {
        const counters = document.querySelectorAll('.counter');
        
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-target'));
            const duration = 2000; // 2 seconds
            const increment = target / (duration / 16); // 60fps
            let current = 0;
            
            const updateCounter = () => {
                current += increment;
                if (current < target) {
                    counter.textContent = Math.floor(current);
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target;
                }
            };
            
            // Start animation when element comes into view
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        updateCounter();
                        observer.unobserve(entry.target);
                    }
                });
            });
            
            observer.observe(counter);
        });
    }
    
    animateCounters();
    
    // Progress bars animation
    function animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        progressBars.forEach(bar => {
            const progress = bar.getAttribute('data-progress');
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        bar.style.width = progress + '%';
                        observer.unobserve(entry.target);
                    }
                });
            });
            
            observer.observe(bar);
        });
    }
    
    animateProgressBars();
    
    // Smooth reveal animation for sections
    function addRevealAnimation() {
        const reveals = document.querySelectorAll('.reveal');
        
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        reveals.forEach(reveal => {
            revealObserver.observe(reveal);
        });
    }
    
    addRevealAnimation();
    
    // Add floating animation to feature icons
    function addFloatingAnimation() {
        const icons = document.querySelectorAll('.feature-icon');
        
        icons.forEach((icon, index) => {
            icon.style.animation = `float 3s ease-in-out infinite`;
            icon.style.animationDelay = `${index * 0.2}s`;
        });
        
        // Add CSS for float animation
        const floatStyle = document.createElement('style');
        floatStyle.textContent = `
            @keyframes float {
                0%, 100% {
                    transform: translateY(0px);
                }
                50% {
                    transform: translateY(-10px);
                }
            }
        `;
        document.head.appendChild(floatStyle);
    }
    
    addFloatingAnimation();
    
    // Theme toggle functionality
    function addThemeToggle() {
        const themeToggle = document.createElement('button');
        themeToggle.innerHTML = '🌙';
        themeToggle.className = 'theme-toggle';
        themeToggle.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 1.5rem;
            cursor: pointer;
            z-index: 1001;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        document.body.appendChild(themeToggle);
        
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            themeToggle.innerHTML = document.body.classList.contains('dark-theme') ? '☀️' : '🌙';
        });
        
        // Dark theme styles
        const darkThemeStyle = document.createElement('style');
        darkThemeStyle.textContent = `
            .dark-theme {
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            
            .dark-theme .navbar {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            }
            
            .dark-theme .overview-card,
            .dark-theme .feature-item,
            .dark-theme .step,
            .dark-theme .api-section,
            .dark-theme .download-item,
            .dark-theme .tech-spec {
                background: #2c2c2c;
                color: #e0e0e0;
            }
            
            .dark-theme .bg-light {
                background-color: #1e1e1e;
            }
            
            .dark-theme .arch-layer {
                background: #2c2c2c;
            }
            
            .dark-theme code {
                background: #2c2c2c;
                color: #ff6b6b;
            }
            
            .dark-theme .step-content pre {
                background: #2c2c2c;
            }
        `;
        document.head.appendChild(darkThemeStyle);
    }
    
    addThemeToggle();
    
    // Back to top button
    function addBackToTop() {
        const backToTop = document.createElement('button');
        backToTop.innerHTML = '↑';
        backToTop.className = 'back-to-top';
        backToTop.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 1.5rem;
            cursor: pointer;
            z-index: 1001;
            transition: all 0.3s ease;
            opacity: 0;
            visibility: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        document.body.appendChild(backToTop);
        
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTop.style.opacity = '1';
                backToTop.style.visibility = 'visible';
            } else {
                backToTop.style.opacity = '0';
                backToTop.style.visibility = 'hidden';
            }
        });
        
        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    addBackToTop();
    
    // Loading screen
    function addLoadingScreen() {
        const loader = document.createElement('div');
        loader.className = 'loader';
        loader.innerHTML = `
            <div class="loader-content">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        `;
        loader.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            transition: opacity 0.5s ease;
        `;
        
        const loaderStyle = document.createElement('style');
        loaderStyle.textContent = `
            .loader-content {
                text-align: center;
                color: white;
            }
            
            .spinner {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(255,255,255,0.3);
                border-top: 4px solid white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(loaderStyle);
        document.body.appendChild(loader);
        
        // Hide loader after page loads
        window.addEventListener('load', () => {
            setTimeout(() => {
                loader.style.opacity = '0';
                setTimeout(() => {
                    loader.remove();
                }, 500);
            }, 1000);
        });
    }
    
    addLoadingScreen();
    
    // Console welcome message
    console.log(`
    🎯 Fan Club MkIV - 智能风扇控制系统
    =====================================
    
    欢迎查看我们的项目！
    
    GitHub: https://github.com/chendashuai/fan-club-master_trae
    文档: 当前页面
    
    如有问题，请在GitHub上提交Issue。
    `);
});

// Error handling for missing elements
window.addEventListener('error', function(e) {
    console.warn('页面加载时出现错误:', e.error);
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(function() {
            const perfData = performance.timing;
            const loadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log(`页面加载时间: ${loadTime}ms`);
        }, 0);
    });
}