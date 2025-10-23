import { useState, useEffect } from "react";
import {
  VStack,
  Flex,
  Button,
  Input,
  Box,
  Select,
  useToast,
} from "@chakra-ui/react";
import { Card } from "../atoms/Card";
import { NewsletterSection } from "../molecules/NewsletterSection";
import { ArrowRightIcon } from "../../assets/icons/ArrowRightIcon";
import { apiService } from "../../services/apiService";
import { newsletterStorage } from "../../services/newsletterStorage";
import type { NewsletterFormData } from "../../types/newsletterForm";

interface CreateNewsletterFormProps {
  onCancel: () => void;
  onNext: (data: NewsletterFormData) => void;
}

export const CreateNewsletterForm = ({
  onCancel,
  onNext,
}: CreateNewsletterFormProps) => {
  const [topic, setTopic] = useState("");
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState("en-US");
  const [html, setHtml] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const toast = useToast();

  // Restaurar dados salvos ao montar o componente
  useEffect(() => {
    const savedData = newsletterStorage.load();
    if (savedData) {
      setTopic(savedData.topic);
      setQuery(savedData.query);
      setLanguage(savedData.language);
      setHtml(savedData.html || "");
    }
  }, []);

  const handleGenerate = async () => {
    if (!topic.trim() || !query.trim()) return;

    // Limpar dados salvos ao gerar nova newsletter
    newsletterStorage.clear();
    
    setIsGenerating(true);
    setHtml("");

    try {
      const result = await apiService.generateNewsletter(topic, query, language);
      setHtml(result.html_content);
    } catch (error) {
      toast({
        title: "Erro ao gerar newsletter",
        description: error instanceof Error ? error.message : "Erro desconhecido",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleNext = () => {
    const formData = {
      topic: topic,
      query: query,
      language: language,
      html: html,
    };
    
    // Salvar dados antes de navegar
    newsletterStorage.save(formData);
    onNext(formData);
  };

  const isFormValid = topic && query && html;

  return (
    <VStack spacing={4} align="stretch">
      <Card>
        <VStack spacing={5} align="stretch">
          <Box fontSize="16px" fontWeight="semibold" color="#111111">
            Newsletter Topic
          </Box>
          <Input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Insert your topic..."
            fontSize="14px"
            height="40px"
            borderColor="gray.200"
            _focus={{ borderColor: "gray.900" }}
            isDisabled={isGenerating}
          />
          <Box fontSize="16px" fontWeight="semibold" color="#111111">
            Newsletter Query
          </Box>
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Insert your query..."
            fontSize="14px"
            height="40px"
            borderColor="gray.200"
            _focus={{ borderColor: "gray.900" }}
            isDisabled={isGenerating}
          />
          <Box fontSize="16px" fontWeight="semibold" color="#111111">
            Language
          </Box>
          <Select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            fontSize="14px"
            height="40px"
            borderColor="gray.200"
            _focus={{ borderColor: "gray.900" }}
            isDisabled={isGenerating}
          >
            <option value="en-US">English (en-US)</option>
            <option value="es-CL">Spanish (es-CL)</option>
            <option value="pt-BR">Portuguese (pt-BR)</option>
          </Select>
        </VStack>
      </Card>

      <Flex justifyContent="flex-end">
        <Button
          onClick={handleGenerate}
          bg="gray.900"
          color="white"
          fontWeight="semibold"
          fontSize="14px"
          height="40px"
          px={4}
          _hover={{ bg: "gray.800" }}
          isLoading={isGenerating}
          isDisabled={!topic.trim() || !query.trim() || isGenerating}
          rightIcon={<ArrowRightIcon />}
        >
          Generate
        </Button>
      </Flex>

      <NewsletterSection
        title="HTML Newsletter"
        content={html}
        onChange={setHtml}
        isLoading={isGenerating && !html}
        loadingText="Perfecting the HTML..."
      />

      {html && (
        <Card>
          <VStack spacing={3} align="stretch">
            <Box fontSize="14px" fontWeight="semibold">
              Preview (rendered HTML)
            </Box>
            <Box
              border="1px solid"
              borderColor="gray.200"
              borderRadius="md"
              p={4}
              fontSize="14px"
              // Sanitize before using in production (e.g., DOMPurify)
              dangerouslySetInnerHTML={{ __html: html }}
            />
          </VStack>
        </Card>
      )}

      <Flex gap={2} justifyContent="flex-end">
        <Button
          onClick={onCancel}
          variant="outline"
          borderColor="gray.200"
          color="gray.800"
          fontWeight="semibold"
          fontSize="14px"
          height="40px"
          _hover={{ bg: "gray.50" }}
        >
          Cancel
        </Button>
        <Button
          onClick={handleNext}
          bg="gray.900"
          color="white"
          fontWeight="semibold"
          fontSize="14px"
          height="40px"
          _hover={{ bg: "gray.800" }}
          isDisabled={!isFormValid}
          opacity={isFormValid ? 1 : 0.3}
        >
          Next: review
        </Button>
      </Flex>
    </VStack>
  );
};
