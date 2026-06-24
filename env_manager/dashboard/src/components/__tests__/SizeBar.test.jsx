import { render } from '@testing-library/react';
import SizeBar from '../SizeBar';

test('renders without crashing', () => {
  const { container } = render(<SizeBar bytes={1024} />);
  expect(container.firstChild).toBeInTheDocument();
});

test('formats bytes correctly', () => {
  const { container } = render(<SizeBar bytes={1_000_000_000} />);
  expect(container.textContent).toContain('1.0 GB');
});
