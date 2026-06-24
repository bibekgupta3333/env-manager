import { render, screen } from '@testing-library/react';
import StatusBadge from '../StatusBadge';

test('renders healthy badge', () => {
  render(<StatusBadge status="healthy" />);
  expect(screen.getByText('healthy')).toBeInTheDocument();
});

test('renders broken badge', () => {
  render(<StatusBadge status="broken" />);
  expect(screen.getByText('broken')).toBeInTheDocument();
});

test('renders stale badge', () => {
  render(<StatusBadge status="stale" />);
  expect(screen.getByText('stale')).toBeInTheDocument();
});
