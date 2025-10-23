import { Textarea, Box } from '@chakra-ui/react';

interface RichTextEditorProps {
  value: string;
  onChange: (value: string) => void;
  minHeight?: string;
}

export const RichTextEditor = ({ value, onChange, minHeight = '500px' }: RichTextEditorProps) => {
  return (
    <Box border="1px solid" borderColor="gray.200" borderRadius="6px" overflow="hidden">
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        minHeight={minHeight}
        border="none"
        borderRadius="0"
        fontSize="14px"
        fontFamily="Consolas, Monaco, 'Courier New', monospace"
        p={4}
        resize="vertical"
        _focus={{ boxShadow: 'none' }}
        placeholder="Enter HTML content..."
        bg="white"
        lineHeight="1.5"
      />
    </Box>
  );
};
