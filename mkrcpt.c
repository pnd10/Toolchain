/*
 * GNU Make Receipter
 * Copyright (c) 2008, Blue Static <http://www.bluestatic.org>
 * 
 * This program is free software; you can redistribute it and/or modify it under the terms of the GNU 
 * General Public License as published by the Free Software Foundation; either version 2 of the 
 * License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without 
 * even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
 * General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along with this program; if not, 
 * write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
 */

#include "receipt.h"
#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <stdlib.h>
#include <assert.h>

int main(int argc, char *argv[])
{
	if (argc < 2)
	{
		printf("Usage: mkrcpt <location to watch>\n");
		return -1;
	}
	
	DIR *dp = opendir(argv[1]);
	if (dp == NULL)
	{
		printf("Could not open the directory\n");
		return -1;
	}
	
	char *recpt = malloc(sizeof(char) * 1024);
	snprintf(recpt, 1024, REPOS_ITEM, getenv("HOME"), "test.rcpt");
			
	FILE *fp = fopen(recpt, "w");
	if (fp == NULL)
	{
		char *repospath = malloc(sizeof(char) * 256);
		snprintf(repospath, 256, REPOS, getenv("HOME"));
		
		// could not open the recipt, try making the directory go again
		DIR *dest = opendir(repospath);
		if (dest == NULL)
		{
			if (mkdir(repospath, 0700) != 0)
			{
				printf("Could not create receipts directory\n");
				free(repospath);
				return -2;
			}
			fp = fopen(recpt, "w");
			if (ferror(fp))
			{
				printf("Failed to create receipt\n");
				free(repospath);
				return -2;
			}
		}
		else
		{
			printf("Failed to create recipt\n");
			free(repospath);
			return -1;
		}
	}
	fwrite(&HEADER, sizeof(HEADER), 1, fp);
	fclose(fp);
	
	
	closedir(dp);
	
	free(recpt);
	
	return 0;
}