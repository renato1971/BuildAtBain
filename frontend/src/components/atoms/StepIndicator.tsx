import { Box, Text } from '@chakra-ui/react';

interface StepIndicatorProps {
  number: number;
  isActive?: boolean;
}

export const StepIndicator = ({ number, isActive = false }: StepIndicatorProps) => {
  return (
    <Box
      width="40px"
      height="40px"
      borderRadius="full"
      border="2px solid"
      borderColor={isActive ? 'gray.900' : 'gray.200'}
      bg={isActive ? 'gray.200' : 'transparent'}
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      <Text
        fontSize="14px"
        fontWeight="semibold"
        color="black"
        lineHeight="20px"
      >
        {number}
      </Text>
    </Box>
  );
};
