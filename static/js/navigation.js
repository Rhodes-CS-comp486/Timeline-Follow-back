function initSidebarNavigation(root = document) {
    const sidebar = root.getElementById ? root.getElementById('siteSidebar') : document.getElementById('siteSidebar');
    const toggleButtons = root.querySelectorAll ? root.querySelectorAll('[data-sidebar-toggle]') : document.querySelectorAll('[data-sidebar-toggle]');
    const closeButtons = root.querySelectorAll ? root.querySelectorAll('[data-sidebar-close]') : document.querySelectorAll('[data-sidebar-close]');

    if (!sidebar || toggleButtons.length === 0 || sidebar.dataset.sidebarReady === 'true') {
        return;
    }

    sidebar.dataset.sidebarReady = 'true';

    const setSidebarState = (isOpen) => {
        document.body.classList.toggle('sidebar-open', isOpen);
        sidebar.setAttribute('aria-hidden', String(!isOpen));

        toggleButtons.forEach((button) => {
            button.setAttribute('aria-expanded', String(isOpen));
            button.classList.toggle('is-open', isOpen);
        });
    };

    toggleButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const isOpen = document.body.classList.contains('sidebar-open');
            setSidebarState(!isOpen);
        });
    });

    closeButtons.forEach((button) => {
        button.addEventListener('click', () => setSidebarState(false));
    });

    sidebar.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => setSidebarState(false));
    });

    if (document.body.dataset.sidebarEscapeBound !== 'true') {
        document.body.dataset.sidebarEscapeBound = 'true';
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                document.body.classList.remove('sidebar-open');
                const openSidebar = document.getElementById('siteSidebar');
                if (openSidebar) {
                    openSidebar.setAttribute('aria-hidden', 'true');
                }
                document.querySelectorAll('[data-sidebar-toggle]').forEach((button) => {
                    button.setAttribute('aria-expanded', 'false');
                    button.classList.remove('is-open');
                });
            }
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initSidebarNavigation());
} else {
    initSidebarNavigation();
}

window.initSidebarNavigation = initSidebarNavigation;
