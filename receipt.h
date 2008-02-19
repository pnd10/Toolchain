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

#include <time.h>

/**
 * Header of the receipt file:
 * [start_of_header]RCPT[record_separator]<file_format_version>[record_separator]
 */
const char HEADER[] = {'\1', 'R', 'C', 'P', 'T', '\30', '1', '\30'};

/**
 * Character constants for the repository of receipts and the path to a receipt item
 */
#ifdef __APPLE__
const char REPOS[] = "%s/Library/mkrcpt";
const char REPOS_ITEM[] = "%s/Library/mkrcpt/%s";
#else
const char REPOS[] = "%s/.mkrcpt";
const char REPOS_ITEM[] = "%s/.mkrcpt/%s";
#endif

/**
 * A record of a file
 */
struct record
{
	char *filename;
	struct timespec modified;
};