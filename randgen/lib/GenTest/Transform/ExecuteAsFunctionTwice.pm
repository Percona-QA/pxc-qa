# Copyright (c) 2008, 2012 Oracle and/or its affiliates. All rights reserved.
# Use is subject to license terms.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301
# USA

package GenTest::Transform::ExecuteAsFunctionTwice;

require Exporter;
@ISA = qw(GenTest GenTest::Transform);

use strict;
use lib 'lib';

use GenTest;
use GenTest::Transform;
use GenTest::Constants;

sub transform {
	my ($class, $orig_query, $executor, $original_result) = @_;

	# We skip: - [OUTFILE | INFILE] queries because these are not data producing and fail (STATUS_ENVIRONMENT_FAILURE)
	return STATUS_WONT_HANDLE if $orig_query =~ m{(OUTFILE|INFILE|PROCESSLIST)}sio
		|| $orig_query !~ m{SELECT}io
		|| $original_result->rows() != 1
		|| $#{$original_result->data()->[0]} != 0;

	my $return_type = $original_result->columnTypes()->[0];
	if ($return_type =~ m{varchar}sgio) {
		# Though the maxium varchar lenght is 65K, we are using 16K to allow up to 4-byte character sets
		$return_type .= "(16000)"
	} elsif ($return_type =~ m{char}sgio) {
		$return_type .= "(255)"
	} elsif ($return_type =~ m{decimal}sgio) {
		# Change type to avoid false compare diffs due to an incorrect decimal type being used when MAX() (and likely other similar functions) is used in the original query. Knowing what is returning decimal type (DBD or MySQL) may allow further improvement.
		$return_type =~ s{decimal}{char (255)}sio
	} elsif (($return_type =~ m{bigint}sgio) && ($orig_query =~ m{BIT_AND\s*\(}sgio)) {
		# BIT_AND returns max value of "unsigned bigint" if there is no match,
		# and this will not fit in (signed) bigint, which is the default return type.
		$return_type = "bigint unsigned";
	}

	return [
		"DROP FUNCTION IF EXISTS stored_func_".abs($$),
		"CREATE FUNCTION stored_func_".abs($$)." () RETURNS $return_type NOT DETERMINISTIC BEGIN DECLARE ret $return_type; $orig_query INTO ret ; RETURN ret; END",
		"SELECT stored_func_".abs($$)."() /* TRANSFORM_OUTCOME_UNORDERED_MATCH */",
                "SELECT stored_func_".abs($$)."() /* TRANSFORM_OUTCOME_UNORDERED_MATCH */",
		"DROP FUNCTION IF EXISTS stored_func_".abs($$)
	];
}

1;
