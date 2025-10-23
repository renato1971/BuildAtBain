import { Box, Container } from '@chakra-ui/react';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout = ({ children }: MainLayoutProps) => {
  return (
    <Box bg="white" minH="100vh" py={8}>
      <Container maxW="1536px" px={8}>
        {children}
      </Container>
    </Box>
  );
};
