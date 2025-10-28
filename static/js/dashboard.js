/**
 * Dashboard JavaScript enhancements for HTMX functionality
 *
 * Provides additional client-side functionality for the dashboard,
 * focusing on improving the user experience with live preview and form handling.
 */

(function() {
    'use strict';

    // Initialize dashboard enhancements when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializePreviewEnhancements();
        initializeFormEnhancements();
        initializeHTMXEnhancements();
    });

    /**
     * Initialize preview panel enhancements
     */
    function initializePreviewEnhancements() {
        const previewPanel = document.querySelector('.preview-panel');
        const contentTextarea = document.getElementById('content');

        if (!previewPanel || !contentTextarea) {
            return; // Not on post edit page
        }

        // Add preview toggle functionality
        addPreviewToggle();

        // Add scroll synchronization
        addScrollSync();

        // Add keyboard shortcuts
        addKeyboardShortcuts();
    }

    /**
     * Add toggle button to show/hide preview panel on smaller screens
     */
    function addPreviewToggle() {
        const previewPanel = document.querySelector('.preview-panel');
        const previewHeader = previewPanel.querySelector('h3');

        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'preview-toggle';
        toggleBtn.innerHTML = '📱';
        toggleBtn.title = 'Toggle preview on mobile';
        toggleBtn.setAttribute('aria-label', 'Toggle preview panel');

        // Add click handler
        toggleBtn.addEventListener('click', function() {
            previewPanel.classList.toggle('preview-hidden');
            toggleBtn.innerHTML = previewPanel.classList.contains('preview-hidden') ? '👁' : '📱';
        });

        // Add to header
        previewHeader.appendChild(toggleBtn);

        // Add CSS for responsive behavior
        const style = document.createElement('style');
        style.textContent = `
            @media (max-width: 1024px) {
                .preview-panel {
                    position: relative;
                    max-height: none;
                    margin-top: 1rem;
                }

                .preview-panel.preview-hidden {
                    display: none;
                }

                .preview-toggle {
                    background: var(--pico-secondary-background-color);
                    border: 1px solid var(--pico-border-color);
                    border-radius: var(--pico-border-radius);
                    padding: 0.25rem 0.5rem;
                    cursor: pointer;
                    font-size: 0.875rem;
                    margin-left: auto;
                }

                .preview-toggle:hover {
                    background: var(--pico-secondary-hover-background-color);
                }
            }

            @media (min-width: 1025px) {
                .preview-toggle {
                    display: none;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Add scroll synchronization between editor and preview
     */
    function addScrollSync() {
        const contentTextarea = document.getElementById('content');
        const previewContainer = document.getElementById('markdown-preview');

        if (!contentTextarea || !previewContainer) return;

        let syncInProgress = false;

        // Sync preview scroll when editor scrolls
        contentTextarea.addEventListener('scroll', function() {
            if (syncInProgress) return;

            const editorScrollPercent = this.scrollTop / (this.scrollHeight - this.clientHeight);
            const previewScrollTop = editorScrollPercent * (previewContainer.scrollHeight - previewContainer.clientHeight);

            syncInProgress = true;
            previewContainer.scrollTop = previewScrollTop;
            setTimeout(() => syncInProgress = false, 100);
        });
    }

    /**
     * Add keyboard shortcuts for enhanced productivity
     */
    function addKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl+/ or Cmd+/ to toggle preview focus
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                togglePreviewFocus();
            }

            // Ctrl+S or Cmd+S to save (if form exists)
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                const postForm = document.getElementById('post-form');
                if (postForm) {
                    e.preventDefault();
                    const submitBtn = postForm.querySelector('button[type="submit"]');
                    if (submitBtn && !submitBtn.disabled) {
                        submitBtn.click();
                    }
                }
            }
        });
    }

    /**
     * Toggle focus between editor and preview
     */
    function togglePreviewFocus() {
        const contentTextarea = document.getElementById('content');
        const previewContainer = document.getElementById('markdown-preview');

        if (document.activeElement === contentTextarea) {
            previewContainer.focus();
            previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            contentTextarea.focus();
        }
    }

    /**
     * Initialize form enhancements
     */
    function initializeFormEnhancements() {
        addAutoSave();
        addUnsavedChangesWarning();
    }

    /**
     * Add auto-save functionality (saves to localStorage)
     */
    function addAutoSave() {
        const postForm = document.getElementById('post-form');
        if (!postForm) return;

        const AUTO_SAVE_KEY = 'mdblog_draft_autosave';
        const AUTO_SAVE_INTERVAL = 30000; // 30 seconds

        // Load saved draft on page load
        const savedDraft = localStorage.getItem(AUTO_SAVE_KEY);
        if (savedDraft) {
            try {
                const draftData = JSON.parse(savedDraft);
                const now = Date.now();

                // Only restore if saved within last hour and form is empty
                if (now - draftData.timestamp < 3600000 && isFormEmpty()) {
                    if (confirm('Found an auto-saved draft. Would you like to restore it?')) {
                        restoreDraft(draftData.data);
                    }
                }
            } catch (e) {
                console.warn('Failed to restore auto-saved draft:', e);
            }
        }

        // Auto-save periodically
        setInterval(function() {
            if (!isFormEmpty() && !postForm.classList.contains('htmx-request')) {
                saveDraft();
            }
        }, AUTO_SAVE_INTERVAL);

        // Save draft when leaving page
        window.addEventListener('beforeunload', saveDraft);

        // Clear auto-save on successful HTMX form submission
        postForm.addEventListener('htmx:afterSwap', function(event) {
            const formMessages = document.getElementById('form-messages');
            if (formMessages && formMessages.innerHTML.includes('alert-success')) {
                // Clear auto-save on successful submission
                localStorage.removeItem(AUTO_SAVE_KEY);
            }
        });

        function isFormEmpty() {
            const formData = new FormData(postForm);
            return !formData.get('title') && !formData.get('content');
        }

        function saveDraft() {
            try {
                // Don't auto-save during HTMX request
                if (postForm.classList.contains('htmx-request')) {
                    return;
                }

                const formData = new FormData(postForm);
                const draftData = {
                    data: {
                        title: formData.get('title'),
                        content: formData.get('content'),
                        description: formData.get('description'),
                        tags: formData.get('tags'),
                        slug: formData.get('new_slug'),
                        draft: document.getElementById('draft').checked
                    },
                    timestamp: Date.now()
                };

                localStorage.setItem(AUTO_SAVE_KEY, JSON.stringify(draftData));
            } catch (e) {
                console.warn('Failed to auto-save draft:', e);
            }
        }

        function restoreDraft(draftData) {
            Object.entries(draftData).forEach(([key, value]) => {
                const input = postForm.querySelector(`[name="${key}"], [name="new_${key}"]`);
                if (input && value !== null && value !== undefined) {
                    if (input.type === 'checkbox') {
                        input.checked = value === true;
                    } else {
                        input.value = value;
                    }
                }
            });

            // Trigger preview update if content was restored
            if (draftData.content) {
                const contentTextarea = document.getElementById('content');
                if (contentTextarea) {
                    htmx.trigger(contentTextarea, 'keyup');
                }
            }
        }
    }

    /**
     * Add warning for unsaved changes
     */
    function addUnsavedChangesWarning() {
        const postForm = document.getElementById('post-form');
        if (!postForm) return;

        let hasUnsavedChanges = false;
        let initialFormData = new FormData(postForm);

        // Track form changes
        postForm.addEventListener('input', function() {
            const currentFormData = new FormData(postForm);
            hasUnsavedChanges = !formDataEqual(initialFormData, currentFormData);
        });

        // Clear warning on successful HTMX submit
        postForm.addEventListener('htmx:afterSwap', function(event) {
            const formMessages = document.getElementById('form-messages');
            if (formMessages && formMessages.innerHTML.includes('alert-success')) {
                hasUnsavedChanges = false;
            }
        });

        // Also clear on regular form submit (fallback)
        postForm.addEventListener('submit', function() {
            hasUnsavedChanges = false;
        });

        // Warn before leaving page
        window.addEventListener('beforeunload', function(e) {
            if (hasUnsavedChanges && !postForm.classList.contains('htmx-request')) {
                e.preventDefault();
                e.returnValue = '';
                return '';
            }
        });

        function formDataEqual(fd1, fd2) {
            const keys1 = Array.from(fd1.keys()).sort();
            const keys2 = Array.from(fd2.keys()).sort();

            if (keys1.length !== keys2.length) return false;

            return keys1.every(key => fd1.get(key) === fd2.get(key));
        }
    }

    /**
     * Initialize HTMX-specific enhancements
     */
    function initializeHTMXEnhancements() {
        // Auto-hide success/error messages after 5 seconds
        document.body.addEventListener('htmx:afterSwap', function(event) {
            autoHideMessages();
        });

        // Show loading indicators for long-running operations
        document.body.addEventListener('htmx:beforeRequest', function(event) {
            const target = event.target;

            // Add subtle loading effects for buttons
            if (target.tagName === 'BUTTON') {
                target.style.opacity = '0.7';
                target.style.cursor = 'wait';
            }
        });

        document.body.addEventListener('htmx:afterRequest', function(event) {
            const target = event.target;

            // Remove loading effects
            if (target.tagName === 'BUTTON') {
                target.style.opacity = '';
                target.style.cursor = '';
            }
        });

        // Handle HTMX errors gracefully
        document.body.addEventListener('htmx:responseError', function(event) {
            console.error('HTMX request failed:', event.detail);
            showErrorMessage('Operation failed. Please try again.');
        });

        document.body.addEventListener('htmx:timeout', function(event) {
            console.warn('HTMX request timed out:', event.detail);
            showErrorMessage('Request timed out. Please check your connection and try again.');
        });

        function autoHideMessages() {
            const containers = ['#success-container', '#error-container', '#form-messages'];

            containers.forEach(selector => {
                const container = document.querySelector(selector);
                if (container && container.innerHTML.trim()) {
                    setTimeout(() => {
                        if (container.innerHTML.includes('alert-success')) {
                            container.innerHTML = '';
                        }
                    }, 5000);
                }
            });
        }

        function showErrorMessage(message) {
            const errorContainer = document.getElementById('error-container') ||
                                 document.getElementById('form-messages');

            if (errorContainer) {
                errorContainer.innerHTML = `<div class="alert alert-error"><p>${message}</p></div>`;
                setTimeout(() => {
                    errorContainer.innerHTML = '';
                }, 5000);
            }
        }
    }

    // Export for potential external use
    window.MDBlogDashboard = {
        togglePreviewFocus: togglePreviewFocus
    };
})();