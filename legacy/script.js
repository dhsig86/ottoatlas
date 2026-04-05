// 1. Defina os dados do seu atlas
// Pode adicionar quantas imagens e descrições quiser aqui.
const atlasData = [
    {
        id: 'normal_01',
        pathology: 'Normal',
        image: 'images/normal_01.jpg',
        description: 'Membrana timpânica translúcida, com marcos anatómicos bem visíveis e cone de luz presente.'
    },
    {
        id: 'oma_01',
        pathology: 'Otite Média Aguda',
        image: 'images/oma_01.jpg',
        description: 'Membrana timpânica abaulada, hiperemiada (avermelhada) e com perda dos marcos anatómicos.'
    },
    {
        id: 'oea_01',
        pathology: 'Otite Externa Aguda',
        image: 'images/oea_01.jpg',
        description: 'Canal auditivo externo edemaciado (inchado) e hiperemiado, com possível presença de secreção.'
    },
    // Adicione mais objetos aqui para cada imagem
];

// 2. Elementos do DOM
const atlasGrid = document.getElementById('atlas-grid');
const modal = document.getElementById('image-modal');
const modalImage = document.getElementById('modal-image');
const modalTitle = document.getElementById('modal-title');
const modalDescription = document.getElementById('modal-description');
const closeButton = document.querySelector('.close-button');

// 3. Função para preencher a grelha do atlas
function populateAtlas() {
    atlasData.forEach(item => {
        const gridItem = document.createElement('div');
        gridItem.className = 'grid-item';
        gridItem.dataset.id = item.id; // Guarda o ID para referência

        gridItem.innerHTML = `
            <img src="${item.image}" alt="${item.pathology}">
            <h3>${item.pathology}</h3>
        `;

        // Adiciona o evento de clique para abrir o modal
        gridItem.addEventListener('click', () => openModal(item));
        
        atlasGrid.appendChild(gridItem);
    });
}

// 4. Funções para controlar o modal
function openModal(item) {
    modalImage.src = item.image;
    modalTitle.textContent = item.pathology;
    modalDescription.textContent = item.description;
    modal.style.display = 'block';
}

function closeModal() {
    modal.style.display = 'none';
}

// Eventos para fechar o modal
closeButton.addEventListener('click', closeModal);
window.addEventListener('click', (event) => {
    if (event.target == modal) {
        closeModal();
    }
});

// Inicia a aplicação
populateAtlas();
