import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Flex, Skeleton, SkeletonText, useToast } from '@chakra-ui/react';
import type { Newsletter } from '../types/newsletter';
import { apiService } from '../services/apiService';
import { MainLayout } from '../components/templates/MainLayout';
import { PageHeader } from '../components/organisms/PageHeader';
import { NewsletterTable } from '../components/organisms/NewsletterTable';

export const Home = () => {
  const navigate = useNavigate();
  const [newsletters, setNewsletters] = useState<Newsletter[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedNewsletters, setSelectedNewsletters] = useState<string[]>([]);
  const toast = useToast();

  useEffect(() => {
    loadNewsletters();
  }, []);

  const loadNewsletters = async () => {
    try {
      setIsLoading(true);
      const data = await apiService.getNewsletters();
      setNewsletters(data);
    } catch (error) {
      toast({
        title: 'Erro ao carregar newsletters',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNewsletter = () => {
    navigate('/create');
  };

  const handleExportData = async () => {
    if (selectedNewsletters.length === 0) {
      toast({
        title: 'Nenhuma newsletter selecionada',
        description: 'Selecione pelo menos uma newsletter para exportar',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      await apiService.exportMultipleNewslettersPDF(selectedNewsletters);
      toast({
        title: `${selectedNewsletters.length} newsletter(s) exportada(s) com sucesso`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      setSelectedNewsletters([]);
    } catch (error) {
      toast({
        title: 'Erro ao exportar newsletters',
        description: 'Não foi possível exportar as newsletters selecionadas',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleSelectNewsletter = (newsletterId: string) => {
    setSelectedNewsletters(prev =>
      prev.includes(newsletterId)
        ? prev.filter(id => id !== newsletterId)
        : [...prev, newsletterId]
    );
  };

  const handleSelectAll = (selected: boolean) => {
    setSelectedNewsletters(selected ? newsletters.map(n => n.id) : []);
  };

  return (
    <MainLayout>
      <PageHeader
        onExportData={handleExportData}
        onCreateNewsletter={handleCreateNewsletter}
        selectedCount={selectedNewsletters.length}
      />
      {isLoading ? (
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
            <Skeleton width="20px" height="20px" />
            <Skeleton width="907px" height="20px" />
            <Skeleton width="150px" height="20px" />
            <Skeleton width="195px" height="20px" />
          </Flex>

          {/* Data Rows */}
          {[...Array(5)].map((_, index) => (
            <Flex
              key={index}
              borderBottom="1px solid"
              borderColor="gray.200"
              py={3}
              px={3}
              gap={4}
              alignItems="center"
            >
              <Skeleton width="20px" height="20px" />
              <Box flex="1" maxW="907px">
                <SkeletonText noOfLines={1} skeletonHeight="3" width="60%" />
              </Box>
              <Box width="150px">
                <SkeletonText noOfLines={1} skeletonHeight="3" width="90%" />
              </Box>
              <Flex width="195px" alignItems="center" gap={2}>
                <Skeleton width="10px" height="10px" borderRadius="full" />
                <SkeletonText noOfLines={1} skeletonHeight="3" width="70px" />
              </Flex>
            </Flex>
          ))}
        </Box>
      ) : (
        <NewsletterTable
          newsletters={newsletters}
          selectedNewsletters={selectedNewsletters}
          onSelectNewsletter={handleSelectNewsletter}
          onSelectAll={handleSelectAll}
        />
      )}
    </MainLayout>
  );
};
