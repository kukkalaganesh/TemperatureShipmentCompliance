-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: cold_chain_compliance
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `complianceresult`
--

DROP TABLE IF EXISTS `complianceresult`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `complianceresult` (
  `compliance_result_id` bigint NOT NULL AUTO_INCREMENT,
  `shipment_id` varchar(25) NOT NULL,
  `evaluated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `compliance_status` enum('COMPLIANT','NON_COMPLIANT','REVIEW_REQUIRED') NOT NULL,
  `issue_codes` json NOT NULL,
  `reading_count` int NOT NULL DEFAULT '0',
  `custody_event_count` int NOT NULL DEFAULT '0',
  `policy_id` varchar(30) DEFAULT NULL,
  `decision_reason` text NOT NULL,
  PRIMARY KEY (`compliance_result_id`),
  KEY `policy_id` (`policy_id`),
  KEY `idx_compliance_shipment_time` (`shipment_id`,`evaluated_at`),
  CONSTRAINT `complianceresult_ibfk_1` FOREIGN KEY (`shipment_id`) REFERENCES `shipment` (`shipment_id`),
  CONSTRAINT `complianceresult_ibfk_2` FOREIGN KEY (`policy_id`) REFERENCES `thresholdpolicy` (`policy_id`),
  CONSTRAINT `complianceresult_chk_1` CHECK ((`reading_count` >= 0)),
  CONSTRAINT `complianceresult_chk_2` CHECK ((`custody_event_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5001 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `custodyevent`
--

DROP TABLE IF EXISTS `custodyevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `custodyevent` (
  `custody_event_id` varchar(30) NOT NULL,
  `shipment_id` varchar(25) NOT NULL,
  `event_time` datetime NOT NULL,
  `from_party` varchar(100) NOT NULL,
  `to_party` varchar(100) NOT NULL,
  `location` varchar(100) NOT NULL,
  `event_type` enum('PICKUP','HANDOFF','DELIVERY','EXCEPTION') NOT NULL,
  PRIMARY KEY (`custody_event_id`),
  KEY `idx_custody_shipment_time` (`shipment_id`,`event_time`),
  CONSTRAINT `custodyevent_ibfk_1` FOREIGN KEY (`shipment_id`) REFERENCES `shipment` (`shipment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `exceptionevent`
--

DROP TABLE IF EXISTS `exceptionevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exceptionevent` (
  `exception_id` bigint NOT NULL AUTO_INCREMENT,
  `shipment_id` varchar(25) NOT NULL,
  `issue_type` enum('LOGGER_NOT_ASSIGNED','PRODUCT_THRESHOLD_MISMATCH','MISSING_DATA_GAP','CUSTODY_GAP','TEMPERATURE_EXCURSION','CALIBRATION_UNCERTAINTY','ROUTE_DWELL') NOT NULL,
  `severity` enum('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL,
  `detected_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `description` text NOT NULL,
  `resolution_status` enum('OPEN','INVESTIGATING','RESOLVED','ACCEPTED') NOT NULL DEFAULT 'OPEN',
  `resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`exception_id`),
  KEY `shipment_id` (`shipment_id`),
  KEY `idx_exceptions_status` (`resolution_status`,`severity`),
  CONSTRAINT `exceptionevent_ibfk_1` FOREIGN KEY (`shipment_id`) REFERENCES `shipment` (`shipment_id`),
  CONSTRAINT `exceptionevent_chk_1` CHECK (((`resolved_at` is null) or (`resolved_at` >= `detected_at`)))
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `excursionreport`
--

DROP TABLE IF EXISTS `excursionreport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `excursionreport` (
  `excursion_id` varchar(30) NOT NULL,
  `shipment_id` varchar(25) NOT NULL,
  `logger_id` varchar(50) NOT NULL,
  `policy_id` varchar(30) NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `duration_minutes` decimal(10,2) NOT NULL,
  `reading_count` int NOT NULL,
  `min_observed_c` decimal(5,2) NOT NULL,
  `max_observed_c` decimal(5,2) NOT NULL,
  `decision` enum('NON_COMPLIANT','EXCURSION_WITHIN_DURATION','REVIEW_REQUIRED') NOT NULL,
  PRIMARY KEY (`excursion_id`),
  KEY `shipment_id` (`shipment_id`),
  KEY `logger_id` (`logger_id`),
  KEY `policy_id` (`policy_id`),
  CONSTRAINT `excursionreport_ibfk_1` FOREIGN KEY (`shipment_id`) REFERENCES `shipment` (`shipment_id`),
  CONSTRAINT `excursionreport_ibfk_2` FOREIGN KEY (`logger_id`) REFERENCES `logger` (`logger_id`),
  CONSTRAINT `excursionreport_ibfk_3` FOREIGN KEY (`policy_id`) REFERENCES `thresholdpolicy` (`policy_id`),
  CONSTRAINT `excursionreport_chk_1` CHECK ((`end_time` >= `start_time`)),
  CONSTRAINT `excursionreport_chk_2` CHECK ((`duration_minutes` >= 0)),
  CONSTRAINT `excursionreport_chk_3` CHECK ((`reading_count` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logger`
--

DROP TABLE IF EXISTS `logger`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `logger` (
  `logger_id` varchar(50) NOT NULL,
  `model` varchar(50) NOT NULL,
  `calibration_date` date NOT NULL,
  `calibration_due` date NOT NULL,
  `calibration_uncertainty_c` decimal(4,2) NOT NULL,
  `logger_status` enum('ACTIVE','MAINTENANCE','RETIRED') NOT NULL,
  PRIMARY KEY (`logger_id`),
  CONSTRAINT `logger_chk_1` CHECK ((`calibration_due` >= `calibration_date`)),
  CONSTRAINT `logger_chk_2` CHECK ((`calibration_uncertainty_c` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `lot`
--

DROP TABLE IF EXISTS `lot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lot` (
  `lot_id` varchar(25) NOT NULL,
  `product_id` varchar(20) NOT NULL,
  `manufacture_date` date NOT NULL,
  `expiry_date` date NOT NULL,
  `lot_status` enum('CREATED','RELEASED','QUARANTINED','EXPIRED') NOT NULL,
  `quantity_units` int NOT NULL,
  PRIMARY KEY (`lot_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `lot_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`),
  CONSTRAINT `lot_chk_1` CHECK ((`expiry_date` >= `manufacture_date`)),
  CONSTRAINT `lot_chk_2` CHECK ((`quantity_units` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `packaging`
--

DROP TABLE IF EXISTS `packaging`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `packaging` (
  `packaging_id` varchar(20) NOT NULL,
  `packaging_type` varchar(50) NOT NULL,
  `capacity_units` int NOT NULL,
  `insulation_rating` decimal(4,3) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`packaging_id`),
  CONSTRAINT `packaging_chk_1` CHECK ((`capacity_units` > 0)),
  CONSTRAINT `packaging_chk_2` CHECK ((`insulation_rating` between 0 and 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `product`
--

DROP TABLE IF EXISTS `product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product` (
  `product_id` varchar(20) NOT NULL,
  `product_name` varchar(100) NOT NULL,
  `category` varchar(50) NOT NULL,
  `min_temp_c` decimal(5,2) NOT NULL,
  `max_temp_c` decimal(5,2) NOT NULL,
  `max_excursion_minutes` int NOT NULL,
  PRIMARY KEY (`product_id`),
  CONSTRAINT `product_chk_1` CHECK ((`min_temp_c` <= `max_temp_c`)),
  CONSTRAINT `product_chk_2` CHECK ((`max_excursion_minutes` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `routestop`
--

DROP TABLE IF EXISTS `routestop`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `routestop` (
  `route_stop_id` varchar(30) NOT NULL,
  `shipment_id` varchar(25) NOT NULL,
  `stop_sequence` int NOT NULL,
  `location` varchar(100) NOT NULL,
  `arrival_time` datetime NOT NULL,
  `departure_time` datetime NOT NULL,
  `dwell_minutes` int NOT NULL,
  PRIMARY KEY (`route_stop_id`),
  UNIQUE KEY `shipment_id` (`shipment_id`,`stop_sequence`),
  CONSTRAINT `routestop_ibfk_1` FOREIGN KEY (`shipment_id`) REFERENCES `shipment` (`shipment_id`),
  CONSTRAINT `routestop_chk_1` CHECK ((`departure_time` >= `arrival_time`)),
  CONSTRAINT `routestop_chk_2` CHECK ((`dwell_minutes` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shipment`
--

DROP TABLE IF EXISTS `shipment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shipment` (
  `shipment_id` varchar(25) NOT NULL,
  `lot_id` varchar(25) NOT NULL,
  `packaging_id` varchar(20) NOT NULL,
  `required_policy_id` varchar(30) NOT NULL,
  `origin` varchar(100) NOT NULL,
  `destination` varchar(100) NOT NULL,
  `planned_departure` datetime NOT NULL,
  `planned_arrival` datetime NOT NULL,
  `actual_departure` datetime DEFAULT NULL,
  `actual_arrival` datetime DEFAULT NULL,
  `shipment_status` enum('PLANNED','IN_TRANSIT','DELIVERED','ON_HOLD','CANCELLED') NOT NULL DEFAULT 'PLANNED',
  `carrier_id` varchar(30) NOT NULL,
  PRIMARY KEY (`shipment_id`),
  KEY `lot_id` (`lot_id`),
  KEY `packaging_id` (`packaging_id`),
  KEY `required_policy_id` (`required_policy_id`),
  CONSTRAINT `shipment_ibfk_1` FOREIGN KEY (`lot_id`) REFERENCES `lot` (`lot_id`),
  CONSTRAINT `shipment_ibfk_2` FOREIGN KEY (`packaging_id`) REFERENCES `packaging` (`packaging_id`),
  CONSTRAINT `shipment_ibfk_3` FOREIGN KEY (`required_policy_id`) REFERENCES `thresholdpolicy` (`policy_id`),
  CONSTRAINT `shipment_chk_1` CHECK ((`planned_arrival` > `planned_departure`)),
  CONSTRAINT `shipment_chk_2` CHECK (((`actual_arrival` is null) or (`actual_departure` is null) or (`actual_arrival` >= `actual_departure`)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shipmentlogger`
--

DROP TABLE IF EXISTS `shipmentlogger`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shipmentlogger` (
  `assignment_id` varchar(30) NOT NULL,
  `shipment_id` varchar(25) NOT NULL,
  `logger_id` varchar(50) NOT NULL,
  `assigned_at` datetime NOT NULL,
  `unassigned_at` datetime DEFAULT NULL,
  `assignment_status` enum('ASSIGNED','UNASSIGNED','REVOKED') NOT NULL DEFAULT 'ASSIGNED',
  PRIMARY KEY (`assignment_id`),
  KEY `shipment_id` (`shipment_id`),
  KEY `logger_id` (`logger_id`),
  CONSTRAINT `shipmentlogger_ibfk_1` FOREIGN KEY (`shipment_id`) REFERENCES `shipment` (`shipment_id`),
  CONSTRAINT `shipmentlogger_ibfk_2` FOREIGN KEY (`logger_id`) REFERENCES `logger` (`logger_id`),
  CONSTRAINT `shipmentlogger_chk_1` CHECK (((`unassigned_at` is null) or (`unassigned_at` >= `assigned_at`)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shipmentstatusevent`
--

DROP TABLE IF EXISTS `shipmentstatusevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shipmentstatusevent` (
  `status_event_id` bigint NOT NULL AUTO_INCREMENT,
  `shipment_id` varchar(25) NOT NULL,
  `previous_status` varchar(30) DEFAULT NULL,
  `new_status` varchar(30) NOT NULL,
  `changed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `changed_by` varchar(100) NOT NULL,
  `reason` text,
  PRIMARY KEY (`status_event_id`),
  KEY `shipment_id` (`shipment_id`),
  CONSTRAINT `shipmentstatusevent_ibfk_1` FOREIGN KEY (`shipment_id`) REFERENCES `shipment` (`shipment_id`)
) ENGINE=InnoDB AUTO_INCREMENT=15001 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `temperaturereading`
--

DROP TABLE IF EXISTS `temperaturereading`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `temperaturereading` (
  `reading_id` varchar(100) NOT NULL,
  `logger_id` varchar(50) NOT NULL,
  `shipment_id` varchar(25) NOT NULL,
  `reading_time` datetime NOT NULL,
  `temperature_c` decimal(5,2) NOT NULL,
  `quality_status` enum('VALID','SUSPECT','INVALID') NOT NULL DEFAULT 'VALID',
  `source` varchar(30) NOT NULL DEFAULT 'SYNTHETIC',
  PRIMARY KEY (`reading_id`),
  UNIQUE KEY `logger_id` (`logger_id`,`shipment_id`,`reading_time`),
  KEY `idx_readings_shipment_time` (`shipment_id`,`reading_time`),
  CONSTRAINT `temperaturereading_ibfk_1` FOREIGN KEY (`logger_id`) REFERENCES `logger` (`logger_id`),
  CONSTRAINT `temperaturereading_ibfk_2` FOREIGN KEY (`shipment_id`) REFERENCES `shipment` (`shipment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `thresholdpolicy`
--

DROP TABLE IF EXISTS `thresholdpolicy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `thresholdpolicy` (
  `policy_id` varchar(30) NOT NULL,
  `product_id` varchar(20) NOT NULL,
  `min_temp_c` decimal(5,2) NOT NULL,
  `max_temp_c` decimal(5,2) NOT NULL,
  `max_excursion_minutes` int NOT NULL,
  `effective_start` datetime NOT NULL,
  `effective_end` datetime DEFAULT NULL,
  `policy_version` int NOT NULL,
  `policy_status` enum('ACTIVE','RETIRED') NOT NULL DEFAULT 'ACTIVE',
  PRIMARY KEY (`policy_id`),
  UNIQUE KEY `product_id` (`product_id`,`policy_version`),
  CONSTRAINT `thresholdpolicy_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`),
  CONSTRAINT `thresholdpolicy_chk_1` CHECK ((`min_temp_c` <= `max_temp_c`)),
  CONSTRAINT `thresholdpolicy_chk_2` CHECK ((`max_excursion_minutes` >= 0)),
  CONSTRAINT `thresholdpolicy_chk_3` CHECK (((`effective_end` is null) or (`effective_end` > `effective_start`)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-29 12:29:21
