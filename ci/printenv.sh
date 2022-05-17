#!/bin/bash

echo -e "\e[0Ksection_start:`date +%s`:environment[collapsed=true]\r\e[0KEnvironment"
printenv
echo -e "\e[0Ksection_end:`date +%s`:environment\r\e[0K"
