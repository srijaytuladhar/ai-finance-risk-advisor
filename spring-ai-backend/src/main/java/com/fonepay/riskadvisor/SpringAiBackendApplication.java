package com.fonepay.riskadvisor;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class SpringAiBackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(SpringAiBackendApplication.class, args);
	}

	@org.springframework.context.annotation.Bean
	public com.fasterxml.jackson.databind.ObjectMapper objectMapper() {
		return new com.fasterxml.jackson.databind.ObjectMapper();
	}

}
