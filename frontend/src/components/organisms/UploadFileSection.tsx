import { useState } from 'react';
import {
  Box,
  Button,
  Flex,
  Heading,
  IconButton,
  Input,
  Text,
  VStack,
  HStack,
  Divider,
  useToast,
  Alert,
  AlertIcon,
  Tooltip,
  Collapse,
  Icon,
} from '@chakra-ui/react';
import { AddIcon, DeleteIcon } from '@chakra-ui/icons';
import { ChevronDownIcon, ChevronRightIcon } from '@chakra-ui/icons';
import { apiService } from '../../services/apiService';

export interface PDFItem {
  url: string;
  filename?: string;
}

type Status = 'idle' | 'uploading' | 'uploaded' | 'running' | 'completed' | 'error';

interface UploadFileSectionProps {
  name: string;
  compact?: boolean;
  defaultOpen?: boolean;
}

export const UploadFileSection = ({ name, compact = false, defaultOpen = true }: UploadFileSectionProps) => {
  // Inicialmente vazio para exigir ação do usuário
  const [items, setItems] = useState<PDFItem[]>([]);
  const [status, setStatus] = useState<Status>('idle');
  const [open, setOpen] = useState(defaultOpen);
  const [jobId, setJobId] = useState<string | null>(null);
  const toast = useToast();

  const isPDF = name.toLowerCase() === 'pdf';
  const hasAtLeastOne = items.length > 0;
  const allUrlsFilled = items.every(i => i.url.trim() !== '');
  const canUpload = hasAtLeastOne && allUrlsFilled && (status === 'idle' || status === 'error');
  const canRun = hasAtLeastOne && status === 'uploaded' && isPDF;
  const disablingAll = status === 'uploading' || status === 'running';

  const updateItem = (index: number, field: keyof PDFItem, value: string) => {
    setItems(prev => {
      const clone = [...prev];
      clone[index] = { ...clone[index], [field]: value };
      return clone;
    });
  };

  const addItem = () => {
    setItems(prev => [...prev, { url: '', filename: '' }]);
  };

  const removeItem = (index: number) => {
    setItems(prev => prev.filter((_, i) => i !== index));
  };

  const pollJobStatus = async (jobId: string, isPDF: boolean) => {
    const maxAttempts = 60; // 5 minutes with 5 second intervals
    let attempts = 0;

    return new Promise<'completed' | 'error'>((resolve) => {
      const interval = setInterval(async () => {
        attempts++;
        
        try {
          if (isPDF) {
            const status = await apiService.getPDFJobStatus(jobId);
            console.log(`[PDF Poll ${attempts}] Status: ${status.status}, Detail: ${status.detail}`);
            
            // PDF upload status: "queued", "downloading", "saved", "ingesting", "done", "error"
            // For PDF UPLOAD, we want to stop at "saved" (not "done")
            if (status.status === 'saved') {
              console.log(`[PDF Upload] Complete - stopping at 'saved'`);
              clearInterval(interval);
              resolve('completed'); // This means upload is complete, ready for Run
            } else if (status.status === 'done') {
              console.log(`[PDF Run] Complete - stopping at 'done'`);
              clearInterval(interval);
              resolve('completed'); // This means run is complete
            } else if (status.status === 'error') {
              console.log(`[PDF] Error detected`);
              clearInterval(interval);
              resolve('error');
            }
          } else {
            const status = await apiService.getIBGEJobStatus(jobId);
            console.log(`[IBGE Poll ${attempts}] Status: ${status.status}, Message: ${status.message}`);
            
            // IBGE status: "pending", "processing", "completed", "failed"
            if (status.status === 'completed') {
              console.log(`[IBGE] Complete - stopping at 'completed'`);
              clearInterval(interval);
              resolve('completed');
            } else if (status.status === 'failed') {
              console.log(`[IBGE] Error detected`);
              clearInterval(interval);
              resolve('error');
            }
          }

          if (attempts >= maxAttempts) {
            clearInterval(interval);
            console.error('Job polling timeout');
            resolve('error');
          }
        } catch (error) {
          console.error('Error polling job status:', error);
          if (attempts >= maxAttempts) {
            clearInterval(interval);
            resolve('error');
          }
        }
      }, 5000);
    });
  };

  // Separate polling function for RUN operation
  const pollRunJobStatus = async (jobId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    return new Promise<'completed' | 'error'>((resolve) => {
      const interval = setInterval(async () => {
        attempts++;
        
        try {
          const status = await apiService.getPDFJobStatus(jobId);
          console.log(`[PDF Run Poll ${attempts}] Status: ${status.status}, Detail: ${status.detail}`);
          
          // For RUN operation, we want "done" status
          if (status.status === 'done') {
            console.log(`[PDF Run] Complete - stopping at 'done'`);
            clearInterval(interval);
            resolve('completed');
          } else if (status.status === 'error') {
            console.log(`[PDF Run] Error detected`);
            clearInterval(interval);
            resolve('error');
          }

          if (attempts >= maxAttempts) {
            clearInterval(interval);
            console.error('Run job polling timeout');
            resolve('error');
          }
        } catch (error) {
          console.error('Error polling run job status:', error);
          if (attempts >= maxAttempts) {
            clearInterval(interval);
            resolve('error');
          }
        }
      }, 5000);
    });
  };

  const handleUpload = async () => {
    if (!canUpload) return;
    console.log(`[${name} Upload] Starting upload...`);
    setStatus('uploading');
    
    try {
      if (isPDF) {
        // PDF Upload
        const result = await apiService.uploadPDFs(items);
        console.log(`[PDF Upload] Started with job_id: ${result.job_id}`);
        setJobId(result.job_id);
        
        // Poll job status - for upload, stop at 'saved'
        const finalStatus = await pollJobStatus(result.job_id, true);
        
        if (finalStatus === 'completed') {
          console.log(`[PDF Upload] Setting status to 'uploaded'`);
          setStatus('uploaded');
          toast({ 
            title: 'Upload concluído', 
            description: 'PDFs salvos com sucesso',
            status: 'success', 
            duration: 3000, 
            isClosable: true 
          });
        } else {
          console.log(`[PDF Upload] Setting status to 'error'`);
          setStatus('error');
          toast({ 
            title: 'Falha no upload', 
            description: 'Erro ao processar PDFs',
            status: 'error', 
            duration: 3000, 
            isClosable: true 
          });
        }
      } else {
        // IBGE Table Upload
        const dataSources = items.map(item => ({
          url: item.url,
          table_name: item.filename || `table_${Date.now()}`
        }));
        
        const result = await apiService.uploadIBGEData(dataSources);
        console.log(`[IBGE Upload] Started with ${result.jobs.length} jobs`);
        
        if (result.jobs.length > 0) {
          // Poll first job status (could be extended to poll all jobs)
          const firstJobId = result.jobs[0].job_id;
          setJobId(firstJobId);
          
          const finalStatus = await pollJobStatus(firstJobId, false);
          
          if (finalStatus === 'completed') {
            console.log(`[IBGE Upload] Processing completed - auto-resetting component`);
            toast({ 
              title: 'Processamento concluído', 
              description: `${result.total} tabela(s) processada(s)`,
              status: 'success', 
              duration: 3000, 
              isClosable: true 
            });
            
            // Auto-reset component after successful IBGE processing
            setTimeout(() => {
              setStatus('idle');
              setJobId(null);
              setItems([]); // Clear all items (URLs and names)
              console.log(`[${name}] Component auto-reset after IBGE completion`);
            }, 2000);
          } else {
            console.log(`[IBGE Upload] Setting status to 'error'`);
            setStatus('error');
            toast({ 
              title: 'Falha no processamento', 
              description: 'Erro ao processar tabelas IBGE',
              status: 'error', 
              duration: 3000, 
              isClosable: true 
            });
          }
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      setStatus('error');
      toast({ 
        title: 'Erro no upload', 
        description: error instanceof Error ? error.message : 'Erro desconhecido',
        status: 'error', 
        duration: 3000, 
        isClosable: true 
      });
    }
  };

  const handleRun = async () => {
    if (!canRun) return;
    console.log(`[PDF Run] Starting run...`);
    setStatus('running');
    
    try {
      const result = await apiService.runPDFProcessing();
      console.log(`[PDF Run] Started with job_id: ${result.job_id}`);
      setJobId(result.job_id);
      
      // Poll job status for RUN operation - now we want "done"
      const finalStatus = await pollRunJobStatus(result.job_id);
      console.log(`[PDF Run] Final status: ${finalStatus}`);

      if (finalStatus === 'completed') {
        console.log(`[PDF Run] Processing completed - auto-resetting component`);
        toast({
          title: 'Processo finalizado',
          description: 'PDFs processados e indexados com sucesso',
          status: 'success', 
          duration: 3000, 
          isClosable: true 
        });
        
        // Auto-reset component after successful PDF run
        setTimeout(() => {
          setStatus('idle');
          setJobId(null);
          setItems([]); // Clear all items (URLs and names)
          console.log(`[${name}] Component auto-reset after PDF run completion`);
        }, 2000);
      } else {
        console.log(`[PDF Run] Setting status to 'error'`);
        setStatus('error');
        toast({ 
          title: 'Falha ao executar', 
          description: 'Erro ao processar PDFs',
          status: 'error', 
          duration: 3000, 
          isClosable: true 
        });
      }
    } catch (error) {
      console.error('Run error:', error);
      setStatus('error');
      toast({ 
        title: 'Erro ao executar', 
        description: error instanceof Error ? error.message : 'Erro desconhecido',
        status: 'error', 
        duration: 3000, 
        isClosable: true 
      });
    }
  };

  // Debug function to force reset
  const handleReset = () => {
    console.log(`[${name}] Manual reset triggered`);
    setStatus('idle');
    setJobId(null);
    toast({
      title: 'Status resetado',
      description: 'Componente foi resetado para estado inicial',
      status: 'info',
      duration: 2000,
      isClosable: true
    });
  };

  return (
    <VStack
      spacing={compact ? '8px' : '16px'}
      align="start"
      width="100%"
    >
      <HStack width="100%" justify="space-between" gap={2}>
        <HStack cursor="pointer" onClick={() => setOpen(o => !o)}>
          <Icon
            as={open ? ChevronDownIcon : ChevronRightIcon}
            boxSize={compact ? 4 : 5}
            color="gray.600"
          />
          <Heading
            as="h2"
            fontSize={compact ? '18px' : '24px'}
            fontWeight="semibold"
            color="#111111"
            lineHeight={compact ? '24px' : '32px'}
          >
            {name}s
          </Heading>
          <Box
            fontSize="11px"
            px="6px"
            py="2px"
            bg="gray.100"
            borderRadius="full"
            color="gray.700"
          >
            {items.length}
          </Box>
        </HStack>

        <Tooltip label={`Adicionar ${name}`} hasArrow>
          <Button
            leftIcon={<AddIcon boxSize={2.5} />}
            size={compact ? 'xs' : 'sm'}
            variant="outline"
            onClick={e => { e.stopPropagation(); addItem(); if (!open) setOpen(true); }}
            isDisabled={disablingAll || status === 'uploaded' || status === 'completed'}
          >
            {compact ? 'Add' : `Adicionar ${name}`}
          </Button>
        </Tooltip>
      </HStack>

      <Text
        fontSize={compact ? '12px' : '16px'}
        color="#111111"
        lineHeight={compact ? '18px' : '24px'}
        display={compact ? 'none' : 'block'}
      >
        Adicione URLs de {name} (e opcionalmente nomes) para enviar ao backend.
      </Text>

      {!hasAtLeastOne && (
        <Alert status="warning" borderRadius="md" py={compact ? 2 : 3}>
          <AlertIcon />
          <Text fontSize={compact ? '12px' : '14px'}>
            Adicione pelo menos um {name} antes de fazer upload ou executar.
          </Text>
        </Alert>
      )}

      <Collapse in={open} style={{ width: '100%' }}>
        <Box
          width="100%"
          maxH={compact ? '220px' : 'none'}
          overflowY={compact ? 'auto' : 'visible'}
          pr={compact ? 1 : 0}
          css={
            compact
              ? {
                  scrollbarWidth: 'thin',
                }
              : undefined
          }
        >
          <VStack spacing={compact ? 2 : 4} width="100%">
            {items.map((item, idx) => (
              <HStack
                key={idx}
                width="100%"
                align="start"
                border="1px solid"
                borderColor="gray.200"
                borderRadius="6px"
                p={compact ? 2 : 4}
                bg="white"
                spacing={compact ? 2 : 4}
              >
                <VStack flex={1} spacing={compact ? 2 : 3} align="stretch">
                  <HStack spacing={compact ? 2 : 3} align="stretch">
                    <Input
                      size={compact ? 'xs' : 'sm'}
                      placeholder={`URL ${name} (obrigatório)`}
                      value={item.url}
                      onChange={e => updateItem(idx, 'url', e.target.value)}
                      isDisabled={disablingAll || status === 'uploaded' || status === 'completed'}
                      fontSize={compact ? '12px' : '14px'}
                    />
                    <Input
                      size={compact ? 'xs' : 'sm'}
                      placeholder="Nome (opcional)"
                      value={item.filename || ''}
                      onChange={e => updateItem(idx, 'filename', e.target.value)}
                      isDisabled={disablingAll || status === 'uploaded' || status === 'completed'}
                      fontSize={compact ? '12px' : '14px'}
                    />
                  </HStack>
                  {!compact && (
                    <Text fontSize="11px" color="gray.500">
                      Preencha a URL.
                    </Text>
                  )}
                </VStack>

                {items.length > 1 && (
                  <IconButton
                    aria-label="Remover"
                    icon={<DeleteIcon />}
                    size={compact ? 'xs' : 'sm'}
                    variant="ghost"
                    colorScheme="red"
                    onClick={() => removeItem(idx)}
                    isDisabled={disablingAll || status === 'uploaded' || status === 'completed'}
                  />
                )}
              </HStack>
            ))}
          </VStack>
        </Box>

        <Divider my={compact ? 2 : 4} />

        <Flex width="100%" justify="flex-end" gap={compact ? 2 : 4} pt={compact ? 0 : 2}>
          <Button
            onClick={handleUpload}
            size={compact ? 'xs' : 'sm'}
            isDisabled={!canUpload || disablingAll}
            isLoading={status === 'uploading'}
            bg="gray.900"
            color="white"
            fontWeight="semibold"
            _hover={{ bg: 'gray.800' }}
            _disabled={{ opacity: 0.35, cursor: 'not-allowed', bg: 'gray.900' }}
          >
            Upload
          </Button>
          {isPDF && (
            <Button
              onClick={handleRun}
              size={compact ? 'xs' : 'sm'}
              isDisabled={!canRun || disablingAll}
              isLoading={status === 'running'}
              bg="gray.900"
              color="white"
              fontWeight="semibold"
              _hover={{ bg: 'gray.800' }}
              _disabled={{ opacity: 0.35, cursor: 'not-allowed', bg: 'gray.900' }}
            >
              Run
            </Button>
          )}
        </Flex>

        {status === 'error' && (
          <Text fontSize="11px" color="red.500" pt={1}>
            Ocorreu um erro. Tente novamente.
          </Text>
        )}
        {status === 'completed' && (
          <Text fontSize="11px" color="green.600" pt={1}>
            Processo concluído com sucesso.
          </Text>
        )}
        {status === 'uploaded' && isPDF && (
          <Text fontSize="11px" color="blue.600" pt={1}>
            Upload concluído. Clique em "Run" para processar.
          </Text>
        )}

        {/* Debug info */}
        {/* {import.meta.env.DEV && (
          <Text fontSize="10px" color="gray.400" pt={1}>
            Debug: Status={status}, JobId={jobId}, canUpload={canUpload.toString()}, canRun={canRun.toString()}
          </Text>
        )} */}
      </Collapse>
    </VStack>
  );
};