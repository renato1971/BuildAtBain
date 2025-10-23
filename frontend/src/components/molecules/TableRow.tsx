import { Tr, Td, Text } from '@chakra-ui/react';
import type { Newsletter } from '../../types/newsletter';
import { TableCheckbox } from '../atoms/TableCheckbox';
import { StatusBadge } from '../atoms/StatusBadge';

interface TableRowProps {
  newsletter: Newsletter;
  isSelected?: boolean;
  onSelect?: (selected: boolean) => void;
}

export const TableRow = ({ newsletter, isSelected, onSelect }: TableRowProps) => {
  return (
    <Tr>
      <Td borderBottom="1px solid" borderColor="gray.200" py="12px" px="12px">
        <TableCheckbox isChecked={isSelected} onChange={onSelect} />
      </Td>
      <Td borderBottom="1px solid" borderColor="gray.200" py="12px" px="12px">
        <Text fontSize="14px" fontWeight="normal" color="black">
          {newsletter.title}
        </Text>
      </Td>
      <Td borderBottom="1px solid" borderColor="gray.200" py="12px" px="12px">
        <Text fontSize="14px" fontWeight="normal" color="black">
          {newsletter.createdAt}
        </Text>
      </Td>
      <Td borderBottom="1px solid" borderColor="gray.200" py="12px" px="12px">
        <StatusBadge status={newsletter.status} />
      </Td>
    </Tr>
  );
};
