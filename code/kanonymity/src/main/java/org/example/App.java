package org.example;

import org.deidentifier.arx.*;
import org.deidentifier.arx.criteria.KAnonymity;
import org.deidentifier.arx.AttributeType.Hierarchy;
import org.deidentifier.arx.metric.Metric;

import java.io.*;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.charset.Charset;
import java.util.*;
import org.deidentifier.arx.risk.*;

public class App {
    public static void main(String[] args) {
        try {
            // Step 1: File path for the original CSV file
            String originalFile = "COVID-19_Treatments_20250203.csv";
            String perturbedFile = "perturbed.csv";

            // Step 2: Read and perturb Latitude/Longitude, then save to new CSV
            List<String[]> perturbedData = new ArrayList<>();

            try (BufferedReader reader = new BufferedReader(new FileReader(originalFile))) {
                String headerLine = reader.readLine();
                if (headerLine == null) throw new RuntimeException("CSV file is empty");

                String[] headers = headerLine.split(",", -1);
                perturbedData.add(headers);

                String line;
                while ((line = reader.readLine()) != null) {
                    String[] row = line.split(",", -1);
                    int latIndex = Arrays.asList(headers).indexOf("Latitude");
                    int lonIndex = Arrays.asList(headers).indexOf("Longitude");

                    if (latIndex >= 0 && lonIndex >= 0 &&
                            row.length > Math.max(latIndex, lonIndex) &&
                            !row[latIndex].isEmpty() && !row[lonIndex].isEmpty()) {
                        try {
                            double lat = Double.parseDouble(row[latIndex]);
                            double lon = Double.parseDouble(row[lonIndex]);

                            double noiseLat = lat + (Math.random() * 0.02 - 0.01);
                            double noiseLon = lon + (Math.random() * 0.02 - 0.01);

                            row[latIndex] = new BigDecimal(noiseLat).setScale(5, RoundingMode.HALF_UP).toString();
                            row[lonIndex] = new BigDecimal(noiseLon).setScale(5, RoundingMode.HALF_UP).toString();
                        } catch (NumberFormatException ignored) {}
                    }
                    perturbedData.add(row);
                }
            }

            // Step 3: Write perturbed data to a new CSV file
            try (PrintWriter writer = new PrintWriter(new FileWriter(perturbedFile))) {
                for (String[] row : perturbedData) {
                    writer.println(String.join(",", row));
                }
            }

            // Step 4: Load perturbed CSV into ARX
            Data data = Data.create(perturbedFile, Charset.defaultCharset(), ',');

            // Step 5: Define generalization hierarchies
            DataHandle handle = data.getHandle();

            // City hierarchy
            Set<String> uniqueCities = new HashSet<>();
            for (int row = 0; row < handle.getNumRows(); row++) {
                uniqueCities.add(handle.getValue(row, handle.getColumnIndexOf("City")));
            }
            Hierarchy.DefaultHierarchy cityHierarchy = Hierarchy.create();
            for (String city : uniqueCities) {
                cityHierarchy.add(city, "Region");
            }
            data.getDefinition().setAttributeType("City", cityHierarchy);

            // State hierarchy
            Set<String> uniqueStates = new HashSet<>();
            for (int row = 0; row < handle.getNumRows(); row++) {
                uniqueStates.add(handle.getValue(row, handle.getColumnIndexOf("State")));
            }
            Hierarchy.DefaultHierarchy stateHierarchy = Hierarchy.create();
            for (String state : uniqueStates) {
                stateHierarchy.add(state, "United States");
            }
            data.getDefinition().setAttributeType("State", stateHierarchy);

            // Zip hierarchy
            Set<String> uniqueZips = new HashSet<>();
            for (int row = 0; row < handle.getNumRows(); row++) {
                uniqueZips.add(handle.getValue(row, handle.getColumnIndexOf("Zip")));
            }
            Hierarchy.DefaultHierarchy zipHierarchy = Hierarchy.create();
            for (String zip : uniqueZips) {
                if (zip != null && zip.length() >= 5) {
                    zipHierarchy.add(zip,
                            zip.substring(0, 5) + "*",
                            zip.substring(0, 3) + "**",
                            zip.substring(0, 2) + "***",
                            "*****");
                }
            }
            data.getDefinition().setAttributeType("Zip", zipHierarchy);

            // Step 6: Configure anonymization
            ARXConfiguration config = ARXConfiguration.create();
            // adjust parameter here!
            config.addPrivacyModel(new KAnonymity(15));
            config.setSuppressionLimit(0.1);;
//            config.setQualityModel(Metric.createLossMetric());
            config.setQualityModel(Metric.createEntropyMetric(true));

            // Step 7: Perform anonymization
            ARXAnonymizer anonymizer = new ARXAnonymizer();
            ARXResult result = anonymizer.anonymize(data, config);

            // Step 8: Output result
            System.out.println("\nAnonymized data:");
            saveHandledDataToCSV(result.getOutput(), "anonymity.csv");

            DataHandle output = result.getOutput();
            if (output != null) {
                System.out.println("\n=== Equivalence Class Statistics ===");
                var eqStats = output.getStatistics().getEquivalenceClassStatistics();
                System.out.println("Average equivalence class size: " + eqStats.getAverageEquivalenceClassSize());
                System.out.println("Maximal equivalence class size: " + eqStats.getMaximalEquivalenceClassSize());
                System.out.println("Minimal equivalence class size: " + eqStats.getMinimalEquivalenceClassSize());
                System.out.println("Number of equivalence classes: " + eqStats.getNumberOfEquivalenceClasses());
                System.out.println("Number of records (excluding suppressed): " + eqStats.getNumberOfRecords());
                System.out.println("Number of suppressed records: " + eqStats.getNumberOfSuppressedRecords());
                System.out.println("Total number of records: " + eqStats.getNumberOfRecordsIncludingSuppressedRecords());

                // Step 9: Re-identification risk analysis
                ARXPopulationModel population = ARXPopulationModel.create(ARXPopulationModel.Region.USA);
                RiskModelAttributes attrModel = output.getRiskEstimator(population).getAttributeRisks();
                RiskModelAttributes.QuasiIdentifierRisk[] attributeRisks = attrModel.getAttributeRisks();
                System.out.println("\n=== Attribute Risks ===");
                for (RiskModelAttributes.QuasiIdentifierRisk qi : attributeRisks) {
                    System.out.println("Attribute: " + qi.getIdentifier());
                    System.out.println(" - Alpha distinction: " + qi.getDistinction());
                    System.out.println(" - Alpha separation: " + qi.getSeparation());
                }


            } else {
                System.out.println("No output found. Possibly no transformation satisfies the privacy model.");
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static void saveHandledDataToCSV(DataHandle handle, String filePath) {
        try (PrintWriter writer = new PrintWriter(new FileWriter(filePath))) {
            for (int col = 0; col < handle.getNumColumns(); col++) {
                writer.print(handle.getAttributeName(col));
                if (col < handle.getNumColumns() - 1) writer.print(",");
            }
            writer.println();

            for (int row = 0; row < handle.getNumRows(); row++) {
                for (int col = 0; col < handle.getNumColumns(); col++) {
                    writer.print(handle.getValue(row, col));
                    if (col < handle.getNumColumns() - 1) writer.print(",");
                }
                writer.println();
            }

            System.out.println("Anonymized data saved to: " + filePath);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
