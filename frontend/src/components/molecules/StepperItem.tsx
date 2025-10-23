import { Box, Text, Flex } from '@chakra-ui/react';
import { StepIndicator } from '../atoms/StepIndicator';

interface StepperItemProps {
  number: number;
  label: string;
  isActive?: boolean;
}

export const StepperItem = ({ number, label, isActive = false }: StepperItemProps) => {
  return (
    <Flex gap={4} alignItems="center">
      <StepIndicator number={number} isActive={isActive} />
      <Box>
        <Text fontSize="14px" fontWeight="semibold" color="black" lineHeight="20px">
          {label}
        </Text>
      </Box>
    </Flex>
  );
};
