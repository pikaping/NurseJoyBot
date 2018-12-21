--
-- Database: `nursejoybot`
--

-- --------------------------------------------------------

--
-- Table structure for table `grupos`
--

CREATE TABLE `grupos` (
  `id` bigint(20) NOT NULL,
  `title` varchar(120) NOT NULL,
  `alias` varchar(60) DEFAULT NULL,
  `spreadsheet` varchar(100) DEFAULT NULL,
  `settings_message` bigint(20) DEFAULT NULL,
  `testgroup` TINYINT NOT NULL DEFAULT '0',
  `candelete` TINYINT NOT NULL DEFAULT '1',
  `locations` TINYINT NOT NULL DEFAULT '1',
  `gymcommand` TINYINT NOT NULL DEFAULT '0',
  `raidcommand` TINYINT NOT NULL DEFAULT '1',
  `talkgroup` VARCHAR(60) NULL DEFAULT NULL,
  `babysitter` TINYINT NOT NULL DEFAULT '0',
  `snail` TINYINT NOT NULL DEFAULT '1',
  `validationrequired` TINYINT NOT NULL DEFAULT '0',
  `timezone` VARCHAR(60) NOT NULL DEFAULT 'Europe/Madrid',
  `banned` TINYINT NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `usuarios`
--

CREATE TABLE `usuarios` (
  `id` bigint(20) NOT NULL,
  `username` varchar(33) DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  `team` enum('Rojo','Azul','Amarillo','') DEFAULT NULL,
  `banned` tinyint(4) NOT NULL DEFAULT '0',
  `trainername` varchar(20) DEFAULT NULL,
  `validation` enum('none','oak','internal') NOT NULL DEFAULT 'none',
  `validation_id` int(11) DEFAULT NULL,
  `admin` TINYINT NOT NULL DEFAULT '0',
  `me` TINYINT NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------


--
-- Table structure for table `validaciones`
--

CREATE TABLE `validaciones` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `startedtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `step` enum('waitingtrainername','waitingscreenshot','failed','expired','completed') NOT NULL DEFAULT 'waitingtrainername',
  `tries` int(11) NOT NULL DEFAULT '0',
  `pokemon` varchar(15) NOT NULL,
  `pokemonname` varchar(15) NOT NULL,
  `trainername` varchar(20) DEFAULT NULL,
  `team` enum('Azul','Rojo','Amarillo','') DEFAULT NULL,
  `level` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--
-- Indexes for dumped tables
--

--
-- Indexes for table `grupos`
--
ALTER TABLE `grupos`
  ADD PRIMARY KEY (`id`);


--
-- Indexes for table `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `trainername` (`trainername`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `validation_id` (`validation_id`);

--
-- Indexes for table `validaciones`
--
ALTER TABLE `validaciones`
  ADD PRIMARY KEY (`id`);


--
-- AUTO_INCREMENT for table `validaciones`
--
ALTER TABLE `validaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;
COMMIT;
