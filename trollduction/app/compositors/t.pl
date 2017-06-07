#!/usr/bin/perl

$i = 0;
foreach $l (`cat t`) {
    $n = sprintf("%.6f", $i++ / 255.0);
    print "($n, $l";
}
