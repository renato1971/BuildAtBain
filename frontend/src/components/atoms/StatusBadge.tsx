import { Badge, Box } from '@chakra-ui/react';
import type { NewsletterStatus } from '../../types/newsletter';

interface StatusBadgeProps {
  status: NewsletterStatus;
}

export const StatusBadge = ({ status }: StatusBadgeProps) => {
  const config = {
    draft: {
      label: 'Draft',
      color: '#FDE047',
    },
    published: {
      label: 'Published',
      color: '#16A34A',
    },
  };

  const { label, color } = config[status];

  return (
    <Box display="flex" alignItems="center" gap={2}>
      <Box
        width="10px"
        height="10px"
        borderRadius="full"
        bg={color}
      />
      <Badge
        fontSize="12px"
        fontWeight="normal"
        bg="transparent"
        color="black"
        p={0}
      >
        {label}
      </Badge>
    </Box>
  );
};
