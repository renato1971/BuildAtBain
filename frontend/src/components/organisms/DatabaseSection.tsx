import { VStack, Heading, Text } from '@chakra-ui/react';
import { FileUpload } from '../molecules/FileUpload';

interface DatabaseSectionProps {
  onFileSelect?: (files: File[]) => void;
}

export const DatabaseSection = ({ onFileSelect }: DatabaseSectionProps) => {
  return (
    <VStack spacing="8px" align="start" width="100%">
      <Heading
        as="h2"
        fontSize="24px"
        fontWeight="semibold"
        color="#111111"
        lineHeight="32px"
      >
        Your databases
      </Heading>
      <Text
        fontSize="16px"
        fontWeight="normal"
        color="#111111"
        lineHeight="24px"
        mb="8px"
      >
        Upload databases to generate charts to compose your newsletter.
      </Text>
      <FileUpload onFileSelect={onFileSelect} />
    </VStack>
  );
};
