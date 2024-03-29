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
#include <sys/stat.h>
#include <unistd.h>

/**
 * Writes out a record struct to the given file pointer
 */
void write_struct(struct record *rec, FILE *fp)
{
	// lay down a record separator
	fputc('\30', fp);
	
	// write the legth of the string
	int pathlen = strlen(rec->filename);
	fwrite(&pathlen, sizeof(size_t), 1, fp);
	
	// put in a unit separator
	fputc('\31', fp);
	
	// write the filename
	fwrite(rec->filename, pathlen + 1, 1, fp);
	
	// another unit separator
	fputc('\31', fp);
	
	// write the modification time
	fwrite(&rec->modified, sizeof(struct timespec), 1, fp);
}

/**
 * Recurses a given directory pointer, and writes data to the file
 * pointer when it finds files
 */
void record_files(char *path, DIR *dp, FILE *fp)
{
	struct dirent *ent;
	while ((ent = readdir(dp)) != NULL)
	{
		// skip dot files
		if (ent->d_name[0] != '.')
		{
			int pathsize = strlen(path) + ent->d_namlen + 2;
			char *newpath = malloc(pathsize * sizeof(char));
			snprintf(newpath, pathsize, "%s/%s", path, ent->d_name);
			
			if (ent->d_type == DT_DIR)
			{
				DIR *ndp = opendir(newpath);
				// we don't have permission, continue
				if (ndp == NULL)
				{
					continue;
				}
				
				record_files(newpath, ndp, fp);
				
				closedir(ndp);
			}
			else
			{
				struct stat info;
				assert(stat(newpath, &info) == 0);
				
				struct record rec;
				rec.filename = newpath;
				rec.modified = info.st_mtimespec;
				
				write_struct(&rec, fp);
			}
			
			free(newpath);
		}
	}
}

/**
 * Compares two lists of files and records the results into the master receipt
 */
void compare_records(FILE *rcpt, FILE *before, FILE *after)
{
	struct record *rbef = malloc(sizeof(struct record));
	struct record *raft = malloc(sizeof(struct record));
	
	while (read_struct(raft, after) == 0)
	{
		assert(read_struct(rbef, before) >= 0);
		
		// if there are new files, go until we're synced up
		while (strcmp(raft->filename, rbef->filename) != 0)
		{
			write_struct(raft, rcpt);
			free(raft->filename);
			if (read_struct(raft, after) != 0)
			{
				free(rbef->filename);
				goto cleanup;
			}
		}
		
		// file was modified, so record it
		if (raft->modified.tv_sec > rbef->modified.tv_sec)
		{
			write_struct(raft, rcpt);
		}
		
		free(raft->filename);
		free(rbef->filename);
	}
	
	cleanup:
		free(rbef);
		free(raft);
}

/**
 * Main method
 */
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
	snprintf(recpt, 1024, REPOS_ITEM, getenv("HOME"), "test");
			
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
	
	time_t install_time;
	assert(time(&install_time) != 0);
	fwrite(&install_time, sizeof(time_t), 1, fp);
	
	fputc('\2', fp);
	
	// open the temporary before list
	int pathsize = strlen(recpt) + 3;
	
	char *temppath = malloc(pathsize * sizeof(char));
	snprintf(temppath, pathsize, "%s.1", recpt);
	FILE *befp = fopen(temppath, "w+");
	record_files(argv[1], dp, befp);
	fputc('\0', befp);
	
	// install
	system("make install");
	
	// open the temporary after list
	rewinddir(dp);
	
	temppath[strlen(temppath) - 1] = '2';
	FILE *affp = fopen(temppath, "w+");
	record_files(argv[1], dp, affp);
	fputc('\0', affp);
	
	// compare the two file lists
	rewind(befp);
	rewind(affp);
	
	compare_records(fp, befp, affp);
	
	fclose(befp);
	fclose(affp);
	
	// remove the two temps
	unlink(temppath);
	temppath[strlen(temppath) - 1] = '1';
	unlink(temppath);
	free(temppath);
	
	// finish cleaning up
	fputc('\0', fp);
	
	fclose(fp);
	closedir(dp);
	
	free(recpt);
	
	return 0;
}