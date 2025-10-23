import { Box } from '@chakra-ui/react';

interface CardProps {
  children: React.ReactNode;
}

export const Card = ({ children }: CardProps) => {
  return (
    <Box
      bg="white"
      p={4}
      borderRadius="6px"
      boxShadow="0px 0px 1px 0px rgba(24, 24, 27, 0.3), 0px 4px 8px 0px rgba(24, 24, 27, 0.1)"
      width="100%"
    >
      {children}
    </Box>
  );
};
