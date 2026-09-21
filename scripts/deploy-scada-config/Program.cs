using Scada.Admin.Project;
using Scada.Config;
using Scada.Data.Adapters;
using Scada.Data.Tables;
using System;
using System.IO;
using System.Xml;

namespace Sparta.ConfigDeployer
{
    internal class Program
    {
        static int Main(string[] args)
        {
            if (args.Length < 2)
            {
                Console.WriteLine("Usage: deploy-scada-config <project-file> <output-dir>");
                return 1;
            }

            string projectFile = Path.GetFullPath(args[0]);
            string outputDir = Path.GetFullPath(args[1]);

            if (!File.Exists(projectFile))
            {
                Console.WriteLine($"Project file not found: {projectFile}");
                return 1;
            }

            Console.WriteLine($"Loading project: {projectFile}");
            ScadaProject project = new();
            project.Load(projectFile);

            Console.WriteLine("Loading configuration database from BaseXML");
            if (!project.ConfigDatabase.Load(out string errMsg))
            {
                Console.WriteLine($"Error loading config database: {errMsg}");
                return 1;
            }

            if (project.Instances.Count == 0)
            {
                Console.WriteLine("No instances found in project");
                return 1;
            }

            ProjectInstance instance = project.Instances[0];
            string instanceDir = Path.Combine(outputDir, "Instances", instance.Name);
            string baseDatDir = Path.Combine(instanceDir, "BaseDAT");
            string serverDir = Path.Combine(instanceDir, "ScadaServer");
            string commDir = Path.Combine(instanceDir, "ScadaComm");

            Directory.CreateDirectory(baseDatDir);
            Directory.CreateDirectory(Path.Combine(serverDir, "Config"));
            Directory.CreateDirectory(Path.Combine(serverDir, "Log"));
            Directory.CreateDirectory(Path.Combine(serverDir, "Mod"));
            Directory.CreateDirectory(Path.Combine(commDir, "Config"));
            Directory.CreateDirectory(Path.Combine(commDir, "Log"));
            Directory.CreateDirectory(Path.Combine(commDir, "Mod"));

            Console.WriteLine($"Saving BaseDAT to: {baseDatDir}");
            foreach (IBaseTable table in project.ConfigDatabase.AllTables)
            {
                string datFileName = Path.Combine(baseDatDir, table.FileNameDat);
                using FileStream stream = new(datFileName, FileMode.Create, FileAccess.Write);
                BaseTableAdapter adapter = new() { Stream = stream };
                adapter.Update(table);
                Console.WriteLine($"  {table.FileNameDat} ({table.ItemCount} items)");
            }

            Console.WriteLine("Copying application configurations");
            CopyDirectory(instance.ServerApp.ConfigDir, Path.Combine(serverDir, "Config"));
            CopyDirectory(instance.CommApp.ConfigDir, Path.Combine(commDir, "Config"));

            Console.WriteLine("Creating instance configuration");
            InstanceConfig instanceConfig = new()
            {
                Culture = "en-GB",
                LogDir = "",
                DefaultConnection = "PostgreConn",
                ActiveStorage = "FileStorage"
            };

            instanceConfig.Connections["PostgreConn"] = new Scada.Dbms.DbConnectionOptions
            {
                Name = "PostgreConn",
                KnownDBMS = Scada.Dbms.KnownDBMS.PostgreSQL,
                Server = "localhost",
                Database = "scada",
                Username = "scada",
                Password = "scada"
            };

            XmlDocument storageXml = new();
            storageXml.LoadXml("<Storage code=\"FileStorage\" />");
            instanceConfig.Storages["FileStorage"] = storageXml.DocumentElement;

            string instanceConfigPath = Path.Combine(instanceDir, "Config", InstanceConfig.DefaultFileName);
            Directory.CreateDirectory(Path.Combine(instanceDir, "Config"));
            if (!instanceConfig.Save(instanceConfigPath, out errMsg))
            {
                Console.WriteLine($"Error saving instance config: {errMsg}");
                return 1;
            }

            Console.WriteLine($"Deployment created at: {outputDir}");
            return 0;
        }

        private static void CopyDirectory(string sourceDir, string destDir)
        {
            if (!Directory.Exists(sourceDir))
                return;

            Directory.CreateDirectory(destDir);
            foreach (string file in Directory.GetFiles(sourceDir, "*", SearchOption.AllDirectories))
            {
                string relativePath = file.Substring(sourceDir.Length).TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
                string destFile = Path.Combine(destDir, relativePath);
                Directory.CreateDirectory(Path.GetDirectoryName(destFile));
                File.Copy(file, destFile, true);
            }
        }
    }
}
