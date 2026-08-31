import { render, screen, fireEvent } from '@testing-library/react';
import SearchInput from '../SearchInput';

test('renders input with placeholder', () => {
  render(<SearchInput placeholder="Search..." />);
  expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
});

test('calls onChange when typing', () => {
  const onChange = vi.fn();
  render(<SearchInput value="" onChange={onChange} />);
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } });
  expect(onChange).toHaveBeenCalledWith('test');
});
