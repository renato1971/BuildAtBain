import { Flex, Box } from '@chakra-ui/react';
import { StepperItem } from '../molecules/StepperItem';

interface Step {
  number: number;
  label: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
}

export const Stepper = ({ steps, currentStep }: StepperProps) => {
  return (
    <Flex alignItems="center" width="100%">
      {steps.map((step, index) => (
        <Flex key={step.number} alignItems="center" flex={1}>
          <StepperItem
            number={step.number}
            label={step.label}
            isActive={currentStep === step.number}
          />
          {index < steps.length - 1 && (
            <Box
              flex={1}
              height="0"
              borderBottom="1px solid"
              borderColor="gray.200"
              mx={3}
            />
          )}
        </Flex>
      ))}
    </Flex>
  );
};
