import { useCallback, useState } from 'react';
import type { DragEvent } from 'react';
import { Box, Text } from '@chakra-ui/react';
import { UploadIcon } from '../../assets/icons/UploadIcon';

interface FileUploadProps {
  onFileSelect?: (files: File[]) => void;
  accept?: string;
}

export const FileUpload = ({
  onFileSelect,
  accept = '.csv,.txt'
}: FileUploadProps) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files) as File[];
    onFileSelect?.(files);
  }, [onFileSelect]);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleClick = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = accept;
    input.multiple = true;
    input.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files) {
        onFileSelect?.(Array.from(target.files));
      }
    };
    input.click();
  }, [accept, onFileSelect]);

  return (
    <Box
      data-testid="file-upload"
      width="360px"
      minHeight="149px"
      border="2px dashed"
      borderColor={isDragOver ? 'gray.300' : 'gray.200'}
      borderRadius="6px"
      bg="white"
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      gap="4px"
      px="12px"
      py="16px"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
      cursor="pointer"
      transition="border-color 0.2s"
      _hover={{
        borderColor: 'gray.300'
      }}
    >
      <UploadIcon />
      <Text
        fontSize="14px"
        fontWeight="semibold"
        color="black"
        lineHeight="20px"
        textAlign="center"
      >
        Drag and drop here to upload
      </Text>
      <Text
        fontSize="14px"
        fontWeight="normal"
        color="black"
        lineHeight="20px"
        textAlign="center"
      >
        .csv, .txt up to 20MB
      </Text>
    </Box>
  );
};
