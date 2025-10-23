import { VStack, Heading, Flex, Spinner, Text } from '@chakra-ui/react';
import { Card } from '../atoms/Card';
import { RichTextEditor } from './RichTextEditor';

interface NewsletterSectionProps {
  title: string;
  content?: string;
  onChange?: (value: string) => void;
  isLoading?: boolean;
  loadingText?: string;
}

export const NewsletterSection = ({
  title,
  content = '',
  onChange,
  isLoading = false,
  loadingText = 'Generating...',
}: NewsletterSectionProps) => {
  return (
    <Card>
      <VStack spacing={5} align="stretch">
        <Heading
          as="h3"
          fontSize="16px"
          fontWeight="semibold"
          color="#111111"
          lineHeight="24px"
        >
          {title}
        </Heading>
        {isLoading ? (
          <Flex alignItems="center" gap={3} py={4}>
            <Spinner size="sm" color="gray.900" />
            <Text fontSize="14px" color="gray.600">
              {loadingText}
            </Text>
          </Flex>
        ) : content ? (
          <RichTextEditor
            value={content}
            onChange={(value) => onChange?.(value)}
            minHeight="150px"
          />
        ) : null}
      </VStack>
    </Card>
  );
};
