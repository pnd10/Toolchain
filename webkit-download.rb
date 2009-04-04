#!/usr/bin/env ruby

require "net/http"
require "FileUtils"

puts "========================================================"
puts "== WebKit Nightly Downloader ==========================="
puts "========================================================"

puts "Opening page..."
nightly_page = Net::HTTP.get("nightly.webkit.org", "/")
puts "\t\tdone"

url = nightly_page.match("<a href=\"(.*)(/files/trunk/mac/WebKit-SVN-r([0-9]*)\.dmg)\"")

if !url
	puts "Could not locate a WebKit image"
	exit
end

puts "Going to download #{url[2]}"

puts "Downloading... "
dmg = File.new("/tmp/webkit-nightly.dmg", "w")
dmg.write(Net::HTTP.get("nightly.webkit.org", url[2]))
dmg.close
puts "\t\tdone"

puts "Attaching DMG..."
attach = %x{hdiutil attach /tmp/webkit-nightly.dmg}
puts "\t\tdone"

device = attach.match("(/dev/disk([0-9]*))")
puts "Attached to #{device[1]}"

if !device
	puts "Device failed to attach, invalid image"
	exit
end

if File.exists?("/Applications/WebKit.app")
	puts "Moving old WebKit to the trash"
	FileUtils.mv("/Applications/WebKit.app", ENV["HOME"] + "/.Trash/WebKit-#{Time.now.year}-#{Time.now.month}-#{Time.now.day}.app")
end

puts "Copying new WebKit..."
FileUtils.cp_r("/Volumes/WebKit/WebKit.app", "/Applications")
puts "\t\tdone"

puts "Detaching DMG..."
%x{hdiutil detach #{device[1]}}
puts "\t\tdone"

FileUtils.rm("/tmp/webkit-nightly.dmg")
puts "Removed downloaded DMG"

puts "========= Webkit Nightly r#{url[3]} Downloaded =========="