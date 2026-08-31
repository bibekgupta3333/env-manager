import { render, screen } from '@testing-library/react';
import EmptyState from '../EmptyState';

test('renders title and description', () => {
  render(<EmptyState title="No data" description="Nothing here yet" />);
  expect(screen.getByText('No data')).toBeInTheDocument();
  expect(screen.getByText('Nothing here yet')).toBeInTheDocument();
});

test('renders action button when provided', () => {
  const action = { label: 'Do something', onClick: () => {} };
  render(<EmptyState title="Empty" description="desc" action={action} />);
  expect(screen.getByText('Do something')).toBeInTheDocument();
});
