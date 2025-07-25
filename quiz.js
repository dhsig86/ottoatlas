// Copiamos os mesmos dados do atlas para o quiz
const quizData = [
    { id: 'normal_01', pathology: 'Normal', image: 'images/normal_01.jpg' },
    { id: 'oma_01', pathology: 'Otite Média Aguda', image: 'images/oma_01.jpg' },
    { id: 'oea_01', pathology: 'Otite Externa Aguda', image: 'images/oea_01.jpg' },
    // Adicione as mesmas imagens e patologias do seu script.js
];

// Elementos do DOM
const quizImage = document.getElementById('quiz-image');
const answerButtonsContainer = document.getElementById('answer-buttons');
const feedbackText = document.getElementById('feedback-text');
const quizContainer = document.getElementById('quiz-container');
const scoreContainer = document.getElementById('score-container');
const finalScore = document.getElementById('final-score');
const restartButton = document.getElementById('restart-button');

let shuffledQuestions, currentQuestionIndex;
let score = 0;

// Função para baralhar um array (algoritmo de Fisher-Yates)
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function startQuiz() {
    score = 0;
    shuffledQuestions =;
    shuffleArray(shuffledQuestions);
    currentQuestionIndex = 0;
    scoreContainer.style.display = 'none';
    quizContainer.style.display = 'block';
    feedbackText.textContent = '';
    setNextQuestion();
}

function setNextQuestion() {
    if (currentQuestionIndex < shuffledQuestions.length) {
        showQuestion(shuffledQuestions[currentQuestionIndex]);
    } else {
        endQuiz();
    }
}

function showQuestion(question) {
    quizImage.src = question.image;
    answerButtonsContainer.innerHTML = ''; // Limpa botões anteriores

    // Criar opções de resposta (1 correta, 3 incorretas)
    const correctAnswer = question.pathology;
    const incorrectAnswers = quizData
       .filter(item => item.pathology!== correctAnswer)
       .map(item => item.pathology);
    
    // Garante que as opções incorretas são únicas
    const uniqueIncorrect =;
    shuffleArray(uniqueIncorrect);
    
    const options = [correctAnswer,...uniqueIncorrect.slice(0, 3)];
    shuffleArray(options);

    options.forEach(option => {
        const button = document.createElement('button');
        button.innerText = option;
        button.classList.add('quiz-button'); // Reutiliza o estilo
        button.addEventListener('click', () => selectAnswer(option, correctAnswer));
        answerButtonsContainer.appendChild(button);
    });
}

function selectAnswer(selectedOption, correctOption) {
    if (selectedOption === correctOption) {
        score++;
        feedbackText.textContent = 'Correto!';
        feedbackText.style.color = 'green';
    } else {
        feedbackText.textContent = `Incorreto. A resposta era: ${correctOption}`;
        feedbackText.style.color = 'red';
    }

    currentQuestionIndex++;
    // Espera um pouco antes de mostrar a próxima pergunta
    setTimeout(() => {
        feedbackText.textContent = '';
        setNextQuestion();
    }, 1500);
}

function endQuiz() {
    quizContainer.style.display = 'none';
    scoreContainer.style.display = 'block';
    finalScore.textContent = `${score} / ${shuffledQuestions.length}`;
}

restartButton.addEventListener('click', startQuiz);

// Inicia o quiz quando a página carrega
startQuiz();
