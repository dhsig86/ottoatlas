import { describe, test, expect, vi, beforeAll } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AtlasQuiz } from './AtlasQuiz';

// Mock do global fetch para simular offline e usar o fallback do quiz de forma limpa
beforeAll(() => {
  global.fetch = vi.fn().mockImplementation(() =>
    Promise.resolve({
      json: () => Promise.resolve({ success: false, cases: [] }),
    })
  ) as any;
});

describe('Componente AtlasQuiz', () => {
  test('deve renderizar a tela inicial com inputs e botões desabilitados por padrão após sair do loading', async () => {
    render(<AtlasQuiz />);

    // Espera sair do estado de carregamento inicial
    const btnClinico = await screen.findByRole('button', { name: /Quiz Clínico/i });
    const btnAnatomico = await screen.findByRole('button', { name: /Quiz Anatômico/i });

    // Verifica título inicial e placeholder
    expect(screen.getByText('Benchmarking Atlas')).toBeDefined();
    expect(screen.getByPlaceholderText(/Ex: Dr. Antônio/i)).toBeDefined();

    // Os botões devem estar desabilitados inicialmente porque o nome do usuário está vazio
    expect(btnClinico.hasAttribute('disabled')).toBe(true);
    expect(btnAnatomico.hasAttribute('disabled')).toBe(true);
  });

  test('deve habilitar os botões do quiz após digitar o nome', async () => {
    render(<AtlasQuiz />);

    // Espera carregar
    const btnClinico = await screen.findByRole('button', { name: /Quiz Clínico/i });
    const btnAnatomico = await screen.findByRole('button', { name: /Quiz Anatômico/i });

    const inputName = screen.getByPlaceholderText(/Ex: Dr. Antônio/i);
    fireEvent.change(inputName, { target: { value: 'Dr. Teste' } });

    expect(btnClinico.hasAttribute('disabled')).toBe(false);
    expect(btnAnatomico.hasAttribute('disabled')).toBe(false);
  });

  test('deve iniciar o quiz clínico ao fornecer nome e clicar no botão correspondente', async () => {
    render(<AtlasQuiz />);

    // Espera carregar
    const btnClinico = await screen.findByRole('button', { name: /Quiz Clínico/i });

    const inputName = screen.getByPlaceholderText(/Ex: Dr. Antônio/i);
    fireEvent.change(inputName, { target: { value: 'Dr. Teste' } });

    fireEvent.click(btnClinico);

    // Deve exibir o indicador de questão
    expect(await screen.findByText(/Questão 1 de/i)).toBeDefined();

    // Deve carregar as opções de resposta
    const optionsHeader = screen.getByRole('heading', { name: /Selecione o diagnóstico assertivo:/i });
    expect(optionsHeader).toBeDefined();
  });
});
