document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const connectBtn = document.getElementById('connectBtn');
    const previewModal = document.getElementById('previewModal');
    const closePreviewBtn = document.getElementById('closePreviewBtn');
    const previewContent = document.getElementById('previewContent');
    const postAdBtn = document.getElementById('postAdBtn');
    const adsContainer = document.getElementById('ads-container');

    // State
    let selectedAd = null;
    let isConnected = false;

    // Load ads when connected
    async function loadAds() {
        try {
            const response = await fetch('/api/robethood/ads');
            const data = await response.json();
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            displayAds(data.ads);
        } catch (error) {
            alert('Fehler beim Laden der Werbeanzeigen: ' + error.message);
        }
    }

    // Display ads in the container
    function displayAds(ads) {
        adsContainer.innerHTML = '';
        ads.forEach(ad => {
            const adCard = document.createElement('div');
            adCard.className = 'border rounded-lg p-4 cursor-pointer hover:bg-gray-50';
            adCard.innerHTML = `
                <img src="${ad.image_url}" alt="${ad.title}" class="w-full h-48 object-cover rounded-lg mb-4">
                <h3 class="font-medium mb-2">${ad.title}</h3>
                <p class="text-gray-600 text-sm mb-4">${ad.description}</p>
                <button class="preview-btn bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 w-full"
                        data-ad-id="${ad.id}">
                    Vorschau
                </button>
            `;
            adsContainer.appendChild(adCard);

            // Add preview button click handler
            const previewBtn = adCard.querySelector('.preview-btn');
            previewBtn.addEventListener('click', () => showPreview(ad));
        });
    }

    // Show ad preview
    function showPreview(ad) {
        selectedAd = ad;
        previewContent.innerHTML = `
            <img src="${ad.image_url}" alt="${ad.title}" class="w-full rounded-lg mb-4">
            <h3 class="font-medium mb-2">${ad.title}</h3>
            <p class="text-gray-600">${ad.description}</p>
        `;
        previewModal.classList.remove('hidden');
    }

    // Connect to API
    connectBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/connect');
            const data = await response.json();
            if (data.status === 'ok') {
                isConnected = true;
                connectBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Verbunden';
                connectBtn.classList.remove('bg-white', 'text-green-600');
                connectBtn.classList.add('bg-green-700', 'text-white');
                loadAds(); // Load ads after successful connection
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            alert('Verbindung fehlgeschlagen: ' + error.message);
        }
    });

    // Close preview modal
    closePreviewBtn.addEventListener('click', () => {
        previewModal.classList.add('hidden');
    });

    // Post selected ad
    postAdBtn.addEventListener('click', async () => {
        if (!selectedAd) {
            alert('Bitte wählen Sie zuerst eine Werbeanzeige aus.');
            return;
        }

        const platforms = Array.from(document.querySelectorAll('input[name="platform"]:checked'))
            .map(checkbox => checkbox.value);

        if (platforms.length === 0) {
            alert('Bitte wählen Sie mindestens eine Plattform aus.');
            return;
        }

        try {
            const response = await fetch('/api/post-ad', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ad_id: selectedAd.id,
                    platforms: platforms
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                alert('Werbeanzeige wurde erfolgreich gepostet!');
                previewModal.classList.add('hidden');
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            alert('Fehler beim Posten der Werbeanzeige: ' + error.message);
        }
    });
});
