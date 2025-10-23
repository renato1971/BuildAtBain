import { Box, Button, Flex, Heading } from '@chakra-ui/react';
import { ShareIcon } from '../../assets/icons/ShareIcon';
import { PlusIcon } from '../../assets/icons/PlusIcon';

interface PageHeaderProps {
  onExportData: () => void;
  onCreateNewsletter: () => void;
  selectedCount?: number;
}

export const PageHeader = ({ onExportData, onCreateNewsletter, selectedCount = 0 }: PageHeaderProps) => {
  return (
    <Flex justifyContent="space-between" alignItems="center" mb={8}>
      <Heading
        as="h1"
        fontSize="36px"
        fontWeight="semibold"
        color="#111111"
        lineHeight="44px"
      >
        My newsletters
      </Heading>

      <Flex gap={4}>
        <Button
          leftIcon={<ShareIcon />}
          onClick={onExportData}
          variant="outline"
          size="md"
          borderColor="gray.300"
          _hover={{ bg: 'gray.50' }}
          isDisabled={selectedCount === 0}
        >
          Export PDF {selectedCount > 0 && `(${selectedCount})`}
        </Button>

        <Button
          onClick={onCreateNewsletter}
          bg="gray.900"
          color="white"
          fontWeight="semibold"
          fontSize="14px"
          height="40px"
          px={4}
          borderRadius="4px"
          leftIcon={
            <Box color="white">
              <PlusIcon />
            </Box>
          }
          _hover={{ bg: 'gray.800' }}
        >
          Create newsletter
        </Button>
      </Flex>
    </Flex>
  );
};
