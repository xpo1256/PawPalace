/**
 * Share functionality for PawPalace
 * Handles sharing dog listings across different platforms
 */

class DogShare {
    constructor() {
        this.init();
    }

    init() {
        // Add event listeners to all share buttons
        document.addEventListener('DOMContentLoaded', () => {
            this.bindShareButtons();
        });
    }

    bindShareButtons() {
        const shareButtons = document.querySelectorAll('[data-share-dog]');
        shareButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const dogName = button.getAttribute('data-dog-name');
                const dogUrl = button.getAttribute('data-dog-url');
                const dogPrice = button.getAttribute('data-dog-price');
                const dogBreed = button.getAttribute('data-dog-breed');
                
                this.shareDog(dogName, dogUrl, dogPrice, dogBreed);
            });
        });
    }

    shareDog(name, url, price, breed) {
        const shareData = {
            title: `Check out ${name} on PawPalace`,
            text: `Adorable ${breed} named ${name} for $${price} - Find your perfect furry friend!`,
            url: url
        };

        // Try native sharing first (mobile devices)
        if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
            navigator.share(shareData)
                .then(() => {
                    this.showNotification('Shared successfully!', 'success');
                })
                .catch((error) => {
                    console.log('Error sharing:', error);
                    this.fallbackShare(shareData);
                });
        } else {
            // Fallback to custom share modal
            this.showShareModal(shareData);
        }
    }

    showShareModal(shareData) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('shareModal');
        if (!modal) {
            modal = this.createShareModal();
            document.body.appendChild(modal);
        }

        // Update modal content
        const titleElement = modal.querySelector('#shareTitle');
        const textElement = modal.querySelector('#shareText');
        const urlElement = modal.querySelector('#shareUrl');

        if (titleElement) titleElement.textContent = shareData.title;
        if (textElement) textElement.textContent = shareData.text;
        if (urlElement) urlElement.value = shareData.url;

        // Show modal
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    createShareModal() {
        const modal = document.createElement('div');
        modal.id = 'shareModal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden';
        
        modal.innerHTML = `
            <div class="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-2xl font-bold text-gray-900">
                        <i class="fas fa-share-alt text-primary-500 mr-2"></i>
                        Share This Dog
                    </h3>
                    <button onclick="this.closest('#shareModal').classList.add('hidden')" 
                            class="text-gray-400 hover:text-gray-600 transition duration-300">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Title</label>
                        <input type="text" id="shareTitle" readonly 
                               class="w-full p-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-600">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                        <textarea id="shareText" readonly rows="3"
                                  class="w-full p-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-600 resize-none"></textarea>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Link</label>
                        <div class="flex">
                            <input type="text" id="shareUrl" readonly 
                                   class="flex-1 p-3 border border-gray-300 rounded-l-lg bg-gray-50 text-gray-600">
                            <button onclick="copyToClipboard('shareUrl')" 
                                    class="px-4 py-3 bg-primary-500 text-white rounded-r-lg hover:bg-primary-600 transition duration-300">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="flex flex-wrap gap-3 mt-6">
                    <button onclick="shareToSocial('facebook', '${shareData.url}', '${shareData.title}')" 
                            class="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition duration-300">
                        <i class="fab fa-facebook-f mr-2"></i> Facebook
                    </button>
                    <button onclick="shareToSocial('twitter', '${shareData.url}', '${shareData.title}')" 
                            class="flex-1 bg-blue-400 text-white py-3 px-4 rounded-lg hover:bg-blue-500 transition duration-300">
                        <i class="fab fa-twitter mr-2"></i> Twitter
                    </button>
                    <button onclick="shareToSocial('whatsapp', '${shareData.url}', '${shareData.text}')" 
                            class="flex-1 bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition duration-300">
                        <i class="fab fa-whatsapp mr-2"></i> WhatsApp
                    </button>
                </div>
                
                <div class="mt-4 text-center">
                    <button onclick="this.closest('#shareModal').classList.add('hidden')" 
                            class="text-gray-500 hover:text-gray-700 transition duration-300">
                        Close
                    </button>
                </div>
            </div>
        `;

        return modal;
    }

    fallbackShare(shareData) {
        // Copy to clipboard as fallback
        this.copyToClipboard(shareData.url);
        this.showNotification('Link copied to clipboard!', 'success');
    }

    copyToClipboard(text) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text)
                .then(() => {
                    this.showNotification('Link copied to clipboard!', 'success');
                })
                .catch(() => {
                    this.legacyCopyToClipboard(text);
                });
        } else {
            this.legacyCopyToClipboard(text);
        }
    }

    legacyCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showNotification('Link copied to clipboard!', 'success');
        } catch (err) {
            this.showNotification('Could not copy to clipboard', 'error');
        }
        
        document.body.removeChild(textArea);
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full ${
            type === 'success' ? 'bg-green-500 text-white' : 
            type === 'error' ? 'bg-red-500 text-white' : 
            'bg-blue-500 text-white'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Global functions for social sharing
function shareToSocial(platform, url, text) {
    const encodedUrl = encodeURIComponent(url);
    const encodedText = encodeURIComponent(text);
    
    let shareUrl = '';
    
    switch (platform) {
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
            break;
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedText}`;
            break;
        case 'whatsapp':
            shareUrl = `https://wa.me/?text=${encodedText}%20${encodedUrl}`;
            break;
        default:
            return;
    }
    
    window.open(shareUrl, '_blank', 'width=600,height=400');
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.select();
        element.setSelectionRange(0, 99999); // For mobile devices
        
        try {
            document.execCommand('copy');
            // Show success notification
            const notification = document.createElement('div');
            notification.className = 'fixed top-4 right-4 z-50 bg-green-500 text-white p-3 rounded-lg shadow-lg';
            notification.innerHTML = '<i class="fas fa-check-circle mr-2"></i>Copied to clipboard!';
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 2000);
        } catch (err) {
            console.error('Could not copy text: ', err);
        }
    }
}

// Initialize the share functionality
const dogShare = new DogShare();

// Lightweight helper for POST with CSRF
function getCookie(name) {
    var value = '; ' + document.cookie;
    var parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function postJSON(url) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin'
    }).then(function(res){ return res.json(); });
}

function bindAccessoryFavoriteToggles(){
    var buttons = document.querySelectorAll('.js-acc-fav-toggle');
    buttons.forEach(function(btn){
        btn.addEventListener('click', function(e){
            e.preventDefault();
            var url = btn.getAttribute('data-fav-url');
            if (!url) return;
            postJSON(url).then(function(data){
                if (data && typeof data.is_favorited !== 'undefined'){
                    btn.classList.toggle('bg-red-100', data.is_favorited);
                    btn.classList.toggle('text-red-600', data.is_favorited);
                    // Update adjacent count if present
                    var countEl = btn.querySelector('.js-acc-fav-count') || btn.closest('[data-acc-card]')?.querySelector('.js-acc-fav-count');
                    if (countEl && typeof data.favorites_count !== 'undefined'){
                        countEl.textContent = data.favorites_count;
                    }
                    // Accessible toast feedback
                    var toast = document.createElement('div');
                    toast.className = 'fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-lg shadow-lg bg-gray-900 text-white';
                    toast.setAttribute('role', 'status');
                    toast.setAttribute('aria-live', 'polite');
                    toast.textContent = data.message || (data.is_favorited ? 'Added to favorites' : 'Removed from favorites');
                    document.body.appendChild(toast);
                    setTimeout(function(){
                        if (toast && toast.parentNode){ toast.parentNode.removeChild(toast); }
                    }, 2200);
                }
            }).catch(function(){ /* ignore */ });
        });
    });
}

if (document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', bindAccessoryFavoriteToggles);
} else {
    bindAccessoryFavoriteToggles();
}
