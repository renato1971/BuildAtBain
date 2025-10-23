import { Box, Flex, Text, Badge } from '@chakra-ui/react';
import { TableCheckbox } from '../atoms/TableCheckbox';
import type { Newsletter } from '../../types/newsletter';

interface NewsletterTableProps {
  newsletters: Newsletter[];
  selectedNewsletters?: string[];
  onSelectNewsletter?: (id: string) => void;
  onSelectAll?: (selected: boolean) => void;
}

export const NewsletterTable = ({ 
  newsletters, 
  selectedNewsletters = [], 
  onSelectNewsletter, 
  onSelectAll 
}: NewsletterTableProps) => {
  const allSelected = newsletters.length > 0 && selectedNewsletters.length === newsletters.length;
  const isIndeterminate = selectedNewsletters.length > 0 && selectedNewsletters.length < newsletters.length;

  const getStatusColor = (status: string) => {
    return status === 'draft' ? 'yellow' : 'green';
  };

  const getStatusLabel = (status: string) => {
    return status === 'draft' ? 'Draft' : 'Published';
  };

  return (
    <Box>
      {/* Header Row */}
      <Flex
        borderBottom="1px solid"
        borderColor="gray.200"
        py={3}
        px={3}
        gap={4}
        alignItems="center"
      >
        <TableCheckbox
          isChecked={allSelected || isIndeterminate}
          onChange={(checked) => onSelectAll?.(checked)}
        />
        <Text fontSize="sm" fontWeight="semibold" color="gray.600" flex="1">
          Title
        </Text>
        <Text fontSize="sm" fontWeight="semibold" color="gray.600" width="150px">
          Created on
        </Text>
        <Text fontSize="sm" fontWeight="semibold" color="gray.600" width="195px">
          Status
        </Text>
      </Flex>

      {/* Data Rows */}
      {newsletters.map((newsletter) => (
        <Flex
          key={newsletter.id}
          borderBottom="1px solid"
          borderColor="gray.200"
          py={3}
          px={3}
          gap={4}
          alignItems="center"
          _hover={{ bg: 'gray.50' }}
        >
          <TableCheckbox
            isChecked={selectedNewsletters.includes(newsletter.id)}
            onChange={() => onSelectNewsletter?.(newsletter.id)}
          />
          <Text fontSize="sm" flex="1" color="gray.700">
            {newsletter.title}
          </Text>
          <Text fontSize="sm" width="150px" color="gray.600">
            {newsletter.createdAt}
          </Text>
          <Flex width="195px" alignItems="center" gap={2}>
            <Box
              width="10px"
              height="10px"
              borderRadius="full"
              bg={`${getStatusColor(newsletter.status)}.400`}
            />
            <Badge
              colorScheme={getStatusColor(newsletter.status)}
              fontSize="xs"
              textTransform="capitalize"
            >
              {getStatusLabel(newsletter.status)}
            </Badge>
          </Flex>
        </Flex>
      ))}
    </Box>
  );
};
