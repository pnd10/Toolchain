require "ftools"
require "Time"

hash = %x{/usr/local/bin/git log -1 --pretty=format:%h}
timestamp = %x{/usr/local/bin/git log -1 --pretty=format:%ct}
time = Time.at(timestamp.to_i)

build = ("%02d" % time.year) + ("%02d" % time.month) + ("%02d" % time.day) + "." + hash

infopath = ENV["CONFIGURATION_BUILD_DIR"] + "/" + ENV["INFOPLIST_PATH"]

file = ""
io = File.new(infopath)
lastline = ""
while line = io.gets do
	if lastline.match("CFBundleVersion")
		file += "\t<string>#{build}</string>\n"
	else
		file += line
	end
	lastline = line
end
io.close

io = File.new(infopath, "w")
io.write(file)
io.close